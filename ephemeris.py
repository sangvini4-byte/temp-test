"""
Тонкая обёртка над pyswisseph.

Если в /app/ephe лежат .se1 файлы — используется полный Swiss Ephemeris.
Если нет — pyswisseph автоматически падает на встроенный Moshier-алгоритм
(точность ~1 угловая секунда для дат 1800-2400, этого достаточно и для
Джйотиш, и для Human Design — оба работают со знаками/градусами, не с
угловыми минутами).
"""
import os
import swisseph as swe

EPHE_PATH = "/app/ephe"
if os.path.isdir(EPHE_PATH) and os.listdir(EPHE_PATH):
    swe.set_ephe_path(EPHE_PATH)
    EPHE_MODE = "swisseph"
else:
    EPHE_MODE = "moshier"

# ВАЖНО: используем TRUE_NODE, а не MEAN_NODE — это стандарт официального
# HD-софта (Jovian Archive / bodygraph.com). Если позже понадобится средний
# узел для другой школы — переключить здесь.
PLANETS = {
    "sun":        swe.SUN,
    "moon":       swe.MOON,
    "mercury":    swe.MERCURY,
    "venus":      swe.VENUS,
    "mars":       swe.MARS,
    "jupiter":    swe.JUPITER,
    "saturn":     swe.SATURN,
    "uranus":     swe.URANUS,
    "neptune":    swe.NEPTUNE,
    "pluto":      swe.PLUTO,
    "node":       swe.TRUE_NODE,
    # Black Moon Lilith:
    # MEAN_APOG  = средняя (используется в большинстве программ и в Джйотиш-подходе).
    # OSCU_APOG  = истинная/осциллирующая (более волатильна, ~±30° от средней).
    # Для реляционного анализа стандартом считается средняя.
    "lilith_mean": swe.MEAN_APOG,
    "lilith_true": swe.OSCU_APOG,
}

FLAGS = swe.FLG_SWIEPH if EPHE_MODE == "swisseph" else swe.FLG_MOSEPH
FLAGS |= swe.FLG_SPEED


def to_jd_ut(year: int, month: int, day: int, hour: float, tz_offset: float) -> float:
    """Локальное время → Julian Day UT."""
    ut_hour = hour - tz_offset
    return swe.julday(year, month, day, ut_hour)


def planet_longitude(jd_ut: float, planet_key: str) -> dict:
    """Геоцентрическая тропическая долгота + скорость (для ретро) одной точки."""
    pid = PLANETS[planet_key]
    pos, _ret_flags = swe.calc_ut(jd_ut, pid, FLAGS)
    lon, lat, dist, speed_lon = pos[0], pos[1], pos[2], pos[3]
    return {
        "longitude": lon % 360.0,
        "latitude": lat,
        "retrograde": speed_lon < 0,
    }


def all_planet_longitudes(jd_ut: float) -> dict:
    """
    Все точки из PLANETS + производные Earth и South Node.

    Lilith_mean и lilith_true включены — используются в Western и Jyotish узлах.
    Human Design фильтрует их самостоятельно (hd_calc.HD_PLANETS).
    """
    result = {}
    for key in PLANETS:
        result[key] = planet_longitude(jd_ut, key)

    # Earth — точно противоположна Солнцу
    result["earth"] = {
        "longitude": (result["sun"]["longitude"] + 180.0) % 360.0,
        "latitude": -result["sun"]["latitude"],
        "retrograde": result["sun"]["retrograde"],
    }
    # South Node — точно противоположен North Node (он же True Node)
    result["south_node"] = {
        "longitude": (result["node"]["longitude"] + 180.0) % 360.0,
        "latitude": -result["node"]["latitude"],
        "retrograde": result["node"]["retrograde"],
    }
    result["north_node"] = result.pop("node")
    return result


def find_design_jd(jd_birth_ut: float) -> float:
    """
    Находит JD момента, когда Солнце было РОВНО на 88° долготы раньше
    натальной позиции — это определение "дизайн"-даты в HD (НЕ "88 дней
    назад", хотя по факту это близко: солнечная дуга в 88° занимает
    87.5-89 суток в зависимости от эллиптичности орбиты Земли).

    Бисекция по Julian Day, точность — до ~1 минуты времени.
    """
    sun_birth = planet_longitude(jd_birth_ut, "sun")["longitude"]
    target = (sun_birth - 88.0) % 360.0

    def angular_diff(jd):
        lon = planet_longitude(jd, "sun")["longitude"]
        diff = (lon - target + 180) % 360 - 180
        return diff

    # Грубая оценка старта поиска: 89 дней назад (среднее значение)
    lo = jd_birth_ut - 92.0
    hi = jd_birth_ut - 86.0

    # Бисекция — angular_diff(lo) и angular_diff(hi) должны иметь разные знаки
    f_lo, f_hi = angular_diff(lo), angular_diff(hi)
    if f_lo * f_hi > 0:
        # Расширяем диапазон на случай нетипичной скорости Солнца
        lo, hi = jd_birth_ut - 95.0, jd_birth_ut - 83.0
        f_lo, f_hi = angular_diff(lo), angular_diff(hi)

    for _ in range(60):  # 60 итераций — точность << 1 секунды
        mid = (lo + hi) / 2.0
        f_mid = angular_diff(mid)
        if abs(f_mid) < 1e-8:
            return mid
        if (f_lo < 0) == (f_mid < 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2.0

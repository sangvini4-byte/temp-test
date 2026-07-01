"""
Джйотиш: сидерические позиции (айянамша Лахири), накшатры, Вимшоттари-даша.

Заменяет HTTP-запросы к Prokerala — расчёт идёт локально через pyswisseph,
без лимитов и без сетевой зависимости.
"""
from datetime import date, timedelta
import swisseph as swe
from . import ephemeris as eph

swe.set_sid_mode(swe.SIDM_LAHIRI)

NAKSHATRAS = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati",
]
NAKSHATRA_SPAN = 360.0 / 27.0   # 13°20'
PADA_SPAN = NAKSHATRA_SPAN / 4.0  # 3°20'

# Цикл владык накшатр (9 планет, повторяется трижды на 27 накшатр)
DASHA_LORD_CYCLE = ["Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury"]
DASHA_YEARS = {
    "Ketu": 7, "Venus": 20, "Sun": 6, "Moon": 10, "Mars": 7,
    "Rahu": 18, "Jupiter": 16, "Saturn": 19, "Mercury": 17,
}
DASHA_TOTAL_YEARS = sum(DASHA_YEARS.values())  # 120
YEAR_DAYS = 365.2425  # григорианский средний год


def get_ayanamsha(jd_ut: float) -> float:
    return swe.get_ayanamsa_ut(jd_ut)


def to_sidereal(tropical_longitude: float, ayanamsha: float) -> float:
    return (tropical_longitude - ayanamsha) % 360.0


def nakshatra_info(sidereal_longitude: float) -> dict:
    idx = int(sidereal_longitude // NAKSHATRA_SPAN)
    within = sidereal_longitude - idx * NAKSHATRA_SPAN
    pada = int(within // PADA_SPAN) + 1
    return {
        "name": NAKSHATRAS[idx],
        "index": idx,
        "pada": min(pada, 4),
        "lord": DASHA_LORD_CYCLE[idx % 9],
    }


def sidereal_planet_positions(jd_ut: float) -> dict:
    ayanamsha = get_ayanamsha(jd_ut)
    tropical = eph.all_planet_longitudes(jd_ut)
    result = {"ayanamsha": round(ayanamsha, 4), "planets": {}}
    for key, data in tropical.items():
        sid_lon = to_sidereal(data["longitude"], ayanamsha)
        entry = {
            "longitude": round(sid_lon, 4),
            "sign_index": int(sid_lon // 30),       # 0=Овен ... 11=Рыбы
            "degree_in_sign": round(sid_lon % 30, 4),
            "retrograde": data["retrograde"],
        }
        if key == "moon":
            entry["nakshatra"] = nakshatra_info(sid_lon)
        result["planets"][key] = entry
    return result


def ascendant_sidereal(jd_ut: float, lat: float, lon: float) -> dict | None:
    """None если время рождения неизвестно — асцендент без времени не считается."""
    try:
        cusps, ascmc = swe.houses_ex(jd_ut, lat, lon, b"P")  # Placidus
    except Exception:
        return None
    ayanamsha = get_ayanamsha(jd_ut)
    tropical_asc = ascmc[0]
    sid_asc = to_sidereal(tropical_asc, ayanamsha)
    return {
        "longitude": round(sid_asc, 4),
        "sign_index": int(sid_asc // 30),
        "degree_in_sign": round(sid_asc % 30, 4),
        "nakshatra": nakshatra_info(sid_asc),
    }


def vimshottari_dasha(moon_sidereal_longitude: float, birth_date: date, lookahead_mahadashas: int = 9) -> dict:
    """
    Полная последовательность Маха-даш от рождения + текущая Маха/Антар-даша.
    Точность дат — на уровне суток (этого достаточно для интерпретации,
    не для электионной астрологии).
    """
    nak = nakshatra_info(moon_sidereal_longitude)
    fraction_elapsed = (moon_sidereal_longitude % NAKSHATRA_SPAN) / NAKSHATRA_SPAN

    start_lord_idx = nak["index"] % 9
    sequence = [DASHA_LORD_CYCLE[(start_lord_idx + i) % 9] for i in range(9)]

    periods = []
    cursor = birth_date
    first_lord = sequence[0]
    first_full_years = DASHA_YEARS[first_lord]
    first_remaining_years = first_full_years * (1 - fraction_elapsed)

    # Первая (текущая на момент рождения) Маха-даша — обрезанная
    end = cursor + timedelta(days=first_remaining_years * YEAR_DAYS)
    periods.append({"lord": first_lord, "start": cursor.isoformat(), "end": end.isoformat(),
                     "full_years": first_full_years})
    cursor = end

    for lord in sequence[1:lookahead_mahadashas]:
        years = DASHA_YEARS[lord]
        end = cursor + timedelta(days=years * YEAR_DAYS)
        periods.append({"lord": lord, "start": cursor.isoformat(), "end": end.isoformat(),
                         "full_years": years})
        cursor = end

    today = date.today()
    current_maha = next((p for p in periods if p["start"] <= today.isoformat() <= p["end"]), None)

    current_antar = None
    if current_maha:
        maha_lord = current_maha["lord"]
        maha_start = date.fromisoformat(current_maha["start"])
        maha_years = (date.fromisoformat(current_maha["end"]) - maha_start).days / YEAR_DAYS

        # Антардаши идут по тому же 9-планетному циклу, начиная с самой Маха-даши
        maha_idx = DASHA_LORD_CYCLE.index(maha_lord)
        antar_sequence = [DASHA_LORD_CYCLE[(maha_idx + i) % 9] for i in range(9)]

        a_cursor = maha_start
        for a_lord in antar_sequence:
            a_years = maha_years * DASHA_YEARS[a_lord] / DASHA_TOTAL_YEARS
            a_end = a_cursor + timedelta(days=a_years * YEAR_DAYS)
            if a_cursor.isoformat() <= today.isoformat() <= a_end.isoformat():
                current_antar = {"lord": a_lord, "start": a_cursor.isoformat(), "end": a_end.isoformat()}
                break
            a_cursor = a_end

    return {
        "nakshatra_at_birth": nak,
        "sequence_from_birth": periods,
        "current_mahadasha": current_maha,
        "current_antardasha": current_antar,
    }

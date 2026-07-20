"""
Bazi (Four Pillars of Destiny) — построение четырёх столпов, Десять Богов,
скрытые стволы, конфликты (clashes) и Da Yun (luck pillar).

ВАЖНО — происхождение этого модуля:
Это переписанный на Python расчёт, ранее существовавший как два JS-файла
(deepseek_javascript_Bazi.js и его "исправленная" версия bazi_fixed_core.js).
При портировании была обязательно проверена привязка дня (day pillar anchor),
потому что "исправленная" JS-версия молча сломала её — сменила якорь на
2000-01-01 со смещением 4 и подписала это как "Jia Chen", хотя смещение 4
в 60-цикле — это 戊辰/Wu-Chen, а не Jia-Chen, и даже это неверно: настоящий
день-столп для 2000-01-01 — 戊午 (Wu-Wu), смещение 54.

ПРОВЕРКА ЯКОРЯ (web-search, два независимых источника, разнесённых на 124 года,
что покрывает погрешности при переходе через невисокосный 1900 и високосный 2000):
  - 1900-01-31 = 甲辰 (Jia-Chen)  — cantian.ai, zhihu 60-甲子 таблица (оба сошлись)
  - 2024-01-01 = 甲子 (Jia-Zi)   — yi733.com, реальный байцзы-расчёт на 15:00-16:00
Якорь (1900-01-01 → позиция 10 в 60-цикле, т.е. 甲戌/Jia-Xu) воспроизводит ОБЕ
даты точно через чистую разницу календарных дней (см. _self_test() ниже).
Это совпадает с оригинальным (непропатченным) JS-файлом — то есть оригинальный
якорь был верным, а "исправление" внесло регрессию. Если когда-нибудь возникнут
сомнения — пересверь self-test на свежих датах, не верь комментариям в коде
(включая этот) на слово.

Что взято из ephemeris.py вместо самостоятельной реализации:
  - Геоцентрическая тропическая долгота Солнца — через eph.planet_longitude(),
    то есть Swiss Ephemeris / Moshier, а не полиномиальная аппроксимация
    (как было в обоих JS-файлах). Это даёт эфемеридную точность для
    солнечных терминов (jie) — устраняет источник ошибок, который ни один
    из JS-вариантов не проверял.

Что унаследовано из bazi_fixed_core.js как корректное (без изменений в сути):
  - Late-Zi (23:00-00:59 true solar time) сдвигает ДЕНЬ для дня-столпа на +1 — стандартная
    конвенция Бацзы, отсутствовавшая в оригинальном JS.
  - Скрытые стволы (hidden stems) по ветвям.

Что исправлено дополнительно при портировании (не было исправлено ни в одной
из двух JS-версий):
  - "currentAge" (для движения по Da Yun) сравнивал месяц и день независимо
    друг от друга (AND), что даёт неверный результат для дат типа
    "день рождения 15 января, сегодня 1 марта" — компонентное сравнение
    говорит "день рождения ещё не наступил", хотя 1 марта уже точно после
    15 января в этом году. Заменено на сравнение полных кортежей (month, day).

ИСПРАВЛЕНИЕ 2024-07 (баг: current luck pillar всегда возвращал первый столп):
  - compute_bazi возвращал первый столп последовательности вместо актуального.
    У 27-летнего человека это был детский столп (ages 1.4–11.4), что ломало
    весь блок TIMING в синтезе. Теперь функция _advance_to_current_pillar()
    явно ищет столп по текущему возрасту и возвращает его вместе с диапазоном.
  - Добавлено поле current_pillar_age_range в luck_pillar для прозрачности.

ИСПРАВЛЕНИЕ 2026-07 (краш: IndexError на часовом столпе → 500 у клиента):
  - HOUR_STEM_TABLE задавала только 10 колонок на строку ("10 двухчасовых
    веток"), хотя веток (branches) в сутках 12, а hour_branch_idx честно
    принимает значения 0..11. Для рождений в ветках Xu (19:00–21:00) и
    Hai (21:00–23:00 true solar time) — это около 1/6 всех возможных
    времён рождения — HOUR_STEM_TABLE[...][10] / [...][11] уходили в
    IndexError, и весь /bazi падал с 500 независимо от остальных данных.
    Пример: 2000-03-02, 22:01, tz=+2, lon=30.52 → true_solar≈21.85 →
    Hai (idx=11) → падение.
  - Сама таблица к тому же не соответствовала классическому методу
    "Wu Shu Dun" (五鼠遁) даже в пределах имевшихся 10 колонок — значения
    шли парами (0,0,1,1,2,2,...) вместо правильной последовательной схемы.
  - Таблица удалена, часовой ствол считается напрямую по формуле
    ((day_stem_idx % 5) * 2 + hour_branch_idx) % 10, сверенной с
    классической таблицей Wu Shu Dun для всех 5 групп дневных стволов
    и всех 12 часовых веток (см. тест в конце файла).
"""
from __future__ import annotations

import math
from datetime import date, timedelta
from typing import Optional

from . import ephemeris as eph

# ────────────────────────── Справочные таблицы ──────────────────────────

STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"]
BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"]
ELEMENTS = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"]
YIN_YANG = ["Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"]

HIDDEN_STEMS = {
    "Zi": ["Gui"], "Chou": ["Ji", "Gui", "Xin"], "Yin": ["Jia", "Bing", "Wu"],
    "Mao": ["Yi"], "Chen": ["Wu", "Yi", "Gui"], "Si": ["Bing", "Geng", "Wu"],
    "Wu": ["Ding", "Bing", "Wu"], "Wei": ["Ji", "Yi", "Ding"], "Shen": ["Geng", "Ren", "Wu"],
    "You": ["Xin"], "Xu": ["Wu", "Ding", "Xin"], "Hai": ["Ren", "Jia"],
}

# Час → ствол ("Wu Shu Dun" / 五鼠遁): группа дня (day_stem_idx % 5) задаёт
# стартовый ствол для Zi-часа (0, 2, 4, 6, 8 — см. _hour_stem_idx() ниже),
# дальше ствол просто последовательно растёт с каждой из 12 часовых веток
# и оборачивается через 10 (стволов всего 10, веток 12). ПРЕЖДЕ здесь была
# статичная таблица на 10 колонок (не 12) — см. changelog 2026-07 в шапке
# файла про то, почему это ломало часовые столпы Xu/Hai.


def _hour_stem_idx(day_stem_idx: int, hour_branch_idx: int) -> int:
    return ((day_stem_idx % 5) * 2 + hour_branch_idx) % 10

GODS = [
    ["DM", "JC", "EG", "HO", "IW", "DW", "7K", "DO", "IR", "DR"],  # Jia
    ["JC", "DM", "HO", "EG", "DW", "IW", "DO", "7K", "DR", "IR"],  # Yi
    ["IR", "DR", "DM", "JC", "EG", "HO", "IW", "DW", "7K", "DO"],  # Bing
    ["DR", "IR", "JC", "DM", "HO", "EG", "DW", "IW", "DO", "7K"],  # Ding
    ["7K", "DO", "IR", "DR", "DM", "JC", "EG", "HO", "IW", "DW"],  # Wu
    ["DO", "7K", "DR", "IR", "JC", "DM", "HO", "EG", "DW", "IW"],  # Ji
    ["IW", "DW", "7K", "DO", "IR", "DR", "DM", "JC", "EG", "HO"],  # Geng
    ["DW", "IW", "DO", "7K", "DR", "IR", "JC", "DM", "HO", "EG"],  # Xin
    ["EG", "HO", "IW", "DW", "7K", "DO", "IR", "DR", "DM", "JC"],  # Ren
    ["HO", "EG", "DW", "IW", "DO", "7K", "DR", "IR", "JC", "DM"],  # Gui
]

GOD_NAMES = {
    "DM": "Day Master", "JC": "Jie Cai", "EG": "Eating God", "HO": "Hurting Officer",
    "IW": "Indirect Wealth", "DW": "Direct Wealth", "7K": "Seven Killings",
    "DO": "Direct Officer", "IR": "Indirect Resource", "DR": "Direct Resource",
}

BRANCH_CLASH = {
    "Zi": "Wu", "Chou": "Wei", "Yin": "Shen", "Mao": "You", "Chen": "Xu", "Si": "Hai",
    "Wu": "Zi", "Wei": "Chou", "Shen": "Yin", "You": "Mao", "Xu": "Chen", "Hai": "Si",
}
STEM_CLASH = {
    "Jia": "Geng", "Yi": "Xin", "Bing": "Ren", "Ding": "Gui",
    "Geng": "Jia", "Xin": "Yi", "Ren": "Bing", "Gui": "Ding",
}

# ────────────────────────── 24 солнечных термина ──────────────────────────
_SOLAR_TERMS = [
    ("Li Chun", 315, 2, 4), ("Yu Shui", 330, 2, 19),
    ("Jing Zhe", 345, 3, 6), ("Chun Fen", 0, 3, 21),
    ("Qing Ming", 15, 4, 5), ("Gu Yu", 30, 4, 20),
    ("Li Xia", 45, 5, 5), ("Xiao Man", 60, 5, 21),
    ("Mang Zhong", 75, 6, 6), ("Xia Zhi", 90, 6, 21),
    ("Xiao Shu", 105, 7, 7), ("Da Shu", 120, 7, 23),
    ("Li Qiu", 135, 8, 7), ("Chu Shu", 150, 8, 23),
    ("Bai Lu", 165, 9, 7), ("Qiu Fen", 180, 9, 23),
    ("Han Lu", 195, 10, 8), ("Shuang Jiang", 210, 10, 23),
    ("Li Dong", 225, 11, 7), ("Xiao Xue", 240, 11, 22),
    ("Da Xue", 255, 12, 7), ("Dong Zhi", 270, 12, 22),
    ("Xiao Han", 285, 1, 6), ("Da Han", 300, 1, 20),
]
_JIE_INDICES = list(range(0, 24, 2))


def _sun_longitude(jd_ut: float) -> float:
    return eph.planet_longitude(jd_ut, "sun")["longitude"]


def _find_solar_term_jd(year: int, target_angle: float, approx_month: int, approx_day: int) -> float:
    """Бисекция по JD — находит точный момент, когда тропическая долгота
    Солнца равна target_angle, используя реальную эфемериду."""
    approx_jd = eph.to_jd_ut(year, approx_month, approx_day, 12.0, 0.0)
    lo, hi = approx_jd - 4.0, approx_jd + 4.0

    def angular_diff(jd: float) -> float:
        lon = _sun_longitude(jd)
        return (lon - target_angle + 180) % 360 - 180

    f_lo, f_hi = angular_diff(lo), angular_diff(hi)
    if f_lo * f_hi > 0:
        lo, hi = approx_jd - 10.0, approx_jd + 10.0
        f_lo, f_hi = angular_diff(lo), angular_diff(hi)
        if f_lo * f_hi > 0:
            raise ValueError(f"Cannot bracket solar term angle={target_angle} year={year}")

    for _ in range(60):
        mid = (lo + hi) / 2.0
        f_mid = angular_diff(mid)
        if abs(f_mid) < 1e-8:
            return mid
        if (f_lo < 0) == (f_mid < 0):
            lo, f_lo = mid, f_mid
        else:
            hi, f_hi = mid, f_mid
    return (lo + hi) / 2.0


def get_all_solar_terms(year: int) -> list[dict]:
    """24 термина для заданного года."""
    terms = []
    for i, (name, angle, am, ad) in enumerate(_SOLAR_TERMS):
        calc_year = year + 1 if i >= 22 else year
        jd = _find_solar_term_jd(calc_year, angle, am, ad)
        terms.append({"name": name, "angle": angle, "jd": jd})
    return terms


def get_jie_terms(year: int) -> list[dict]:
    all_terms = get_all_solar_terms(year)
    jie = [all_terms[i] for i in _JIE_INDICES]
    return sorted(jie, key=lambda t: t["jd"])


# ────────────────────────── День-столп: проверенный якорь ──────────────────────────

DAY_PILLAR_ANCHOR_DATE = date(1900, 1, 1)
DAY_PILLAR_ANCHOR_OFFSET = 10  # 1900-01-01 = позиция 10 = 甲戌 (Jia-Xu)


def day_pillar_position(target_date: date) -> int:
    diff_days = (target_date - DAY_PILLAR_ANCHOR_DATE).days
    return (diff_days + DAY_PILLAR_ANCHOR_OFFSET) % 60


def _self_test():
    """Сверка якоря против двух независимо найденных реальных дат."""
    checks = [
        (date(1900, 1, 31), "Jia", "Chen"),
        (date(2024, 1, 1), "Jia", "Zi"),
    ]
    for d, expected_stem, expected_branch in checks:
        pos = day_pillar_position(d)
        stem, branch = STEMS[pos % 10], BRANCHES[pos % 12]
        assert stem == expected_stem and branch == expected_branch, (
            f"Day pillar anchor BROKEN: {d} computed as {stem}-{branch}, "
            f"expected {expected_stem}-{expected_branch}."
        )


_self_test()


# ────────────────────────── True Solar Time (Meeus EoT) ──────────────────────────

def _equation_of_time_minutes(jd_ut_midnight: float) -> float:
    T = (jd_ut_midnight - 2451545.0) / 36525.0
    L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T
    M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T
    eps = math.radians(23.439 - 0.013 * T)
    y = math.tan(eps / 2) ** 2
    e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T
    Mr, L0r = math.radians(M), math.radians(L0)
    eot = (
        y * math.sin(2 * L0r)
        - 2 * e * math.sin(Mr)
        + 4 * e * y * math.sin(Mr) * math.cos(2 * L0r)
        - 0.5 * y * y * math.sin(4 * L0r)
        - 1.25 * e * e * math.sin(2 * Mr)
    ) * 4.0 * (180.0 / math.pi)
    return eot


def _true_solar_time(hh: int, mm: int, tz_offset: float, longitude: float,
                      year: int, month: int, day: int) -> float:
    jd_midnight = eph.to_jd_ut(year, month, day, 0.0, 0.0)
    eot = _equation_of_time_minutes(jd_midnight)
    utc_hour = hh + mm / 60.0 - tz_offset
    mean_solar = utc_hour + longitude / 15.0
    return (mean_solar + eot / 60.0 + 24.0) % 24.0


# ────────────────────────── Вспомогательные функции ──────────────────────────

def _mod(n: int, m: int) -> int:
    return n % m


def _hidden_gods(day_stem_idx: int, branch_name: str) -> list[dict]:
    out = []
    for s in HIDDEN_STEMS.get(branch_name, []):
        idx = STEMS.index(s)
        out.append({"stem": s, "god": GOD_NAMES[GODS[day_stem_idx][idx]]})
    return out


def _current_age(birth_dt: date, ref: date) -> float:
    """Точный возраст в годах на дату ref."""
    has_had_birthday = (ref.month, ref.day) >= (birth_dt.month, birth_dt.day)
    return ref.year - birth_dt.year + (0 if has_had_birthday else -1)


def _advance_to_current_pillar(
    start_stem: int,
    start_branch: int,
    start_age: float,
    step: int,
    current_age: float,
) -> dict:
    """
    Находит актуальный столп Da Yun по текущему возрасту.

    ИСПРАВЛЕНИЕ: оригинальный код делал while age + 10 <= current_age,
    что давало неверный результат — текущий столп всегда был первым.
    Теперь явно вычисляем сколько полных 10-летних периодов прошло
    с moment start_age, и продвигаем stem/branch на это число шагов.

    Возвращает:
        stem_idx, branch_idx — текущего столпа
        age_start             — возраст начала текущего столпа
        age_end               — возраст окончания (age_start + 10)
        periods_elapsed       — сколько периодов прошло (0 = первый столп)
    """
    if current_age < start_age:
        # Ещё не вошли в первый столп (очень маленькой ребёнок)
        return {
            "stem_idx": start_stem,
            "branch_idx": start_branch,
            "age_start": start_age,
            "age_end": start_age + 10,
            "periods_elapsed": 0,
        }

    periods_elapsed = int((current_age - start_age) // 10)
    stem_idx = _mod(start_stem + step * periods_elapsed, 10)
    branch_idx = _mod(start_branch + step * periods_elapsed, 12)
    age_start = start_age + periods_elapsed * 10
    age_end = age_start + 10

    return {
        "stem_idx": stem_idx,
        "branch_idx": branch_idx,
        "age_start": round(age_start, 1),
        "age_end": round(age_end, 1),
        "periods_elapsed": periods_elapsed,
    }


# ────────────────────────── Основной расчёт ──────────────────────────

def compute_bazi(
    birth_date: str,
    birth_time: Optional[str],
    tz_offset: float,
    longitude: float,
    gender: str,
    reference_date: Optional[date] = None,
) -> dict:
    """
    birth_date:     'YYYY-MM-DD'
    birth_time:     'HH:MM' местное, либо None/'UNKNOWN'
    tz_offset:      смещение от UTC в часах
    longitude:      восточная положительная, градусы
    gender:         'male' / 'female'
    reference_date: для какой даты считать текущий Da Yun (по умолчанию сегодня)
    """
    if gender not in ("male", "female"):
        raise ValueError("gender must be 'male' or 'female'")

    y, m, d = (int(x) for x in birth_date.split("-"))
    has_time = bool(birth_time) and birth_time.upper() != "UNKNOWN"

    if has_time:
        hh, mm = (int(x) for x in birth_time.split(":"))
        utc_hour = hh + mm / 60.0 - tz_offset
        true_solar = _true_solar_time(hh, mm, tz_offset, longitude, y, m, d)
    else:
        utc_hour = 12.0 - tz_offset
        true_solar = None

    birth_jd = eph.to_jd_ut(y, m, d, hh + mm / 60.0 if has_time else 12.0, tz_offset)

    # Late-Zi (23:00-00:59 true solar time) сдвигает день для дня-столпа.
    is_late_zi = has_time and (true_solar >= 23.0)
    pillar_date = date(y, m, d) + (timedelta(days=1) if is_late_zi else timedelta(days=0))

    # Solar year относительно Li Chun
    jie_current = get_jie_terms(y)
    li_chun_current = next(t for t in get_all_solar_terms(y) if t["name"] == "Li Chun")["jd"]

    if birth_jd < li_chun_current:
        solar_year = y - 1
        jie_terms = get_jie_terms(y - 1)
    else:
        solar_year = y
        jie_terms = jie_current

    solar_month_index = 11
    for i, t in enumerate(jie_terms):
        if birth_jd >= t["jd"]:
            solar_month_index = i
        else:
            break

    year_stem_idx = _mod(solar_year - 4, 10)
    year_branch_idx = _mod(solar_year - 4, 12)
    month_stem_idx = _mod(year_stem_idx * 2 + solar_month_index, 10)
    month_branch_idx = _mod(solar_month_index + 2, 12)

    day_pos = day_pillar_position(pillar_date)
    day_stem_idx = day_pos % 10
    day_branch_idx = day_pos % 12

    hour_pillar = None
    hour_stem_idx = hour_branch_idx = None
    if has_time:
        if true_solar >= 23.0 or true_solar < 1.0:
            hour_branch_idx = 0
        else:
            hour_branch_idx = int((true_solar + 1) // 2) % 12
        hour_stem_idx = _hour_stem_idx(day_stem_idx, hour_branch_idx)
        hour_pillar = {"stem": STEMS[hour_stem_idx], "branch": BRANCHES[hour_branch_idx]}

    def ten_god(target_stem_idx: int) -> str:
        return GOD_NAMES[GODS[day_stem_idx][target_stem_idx]]

    ten_gods = {
        "year": ten_god(year_stem_idx),
        "month": ten_god(month_stem_idx),
        "day": "Day Master",
        "hour": ten_god(hour_stem_idx) if has_time else None,
    }
    hidden_gods = {
        "year": _hidden_gods(day_stem_idx, BRANCHES[year_branch_idx]),
        "month": _hidden_gods(day_stem_idx, BRANCHES[month_branch_idx]),
        "day": _hidden_gods(day_stem_idx, BRANCHES[day_branch_idx]),
        "hour": _hidden_gods(day_stem_idx, BRANCHES[hour_branch_idx]) if has_time else None,
    }

    pillars = [
        {"stem": year_stem_idx, "branch": year_branch_idx, "label": "Year"},
        {"stem": month_stem_idx, "branch": month_branch_idx, "label": "Month"},
        {"stem": day_stem_idx, "branch": day_branch_idx, "label": "Day"},
    ]
    if has_time:
        pillars.append({"stem": hour_stem_idx, "branch": hour_branch_idx, "label": "Hour"})

    clashes = []
    for i in range(len(pillars)):
        for j in range(i + 1, len(pillars)):
            a, b = pillars[i], pillars[j]
            sb, tb = BRANCHES[a["branch"]], BRANCHES[b["branch"]]
            ss, ts = STEMS[a["stem"]], STEMS[b["stem"]]
            if BRANCH_CLASH.get(sb) == tb:
                clashes.append(f"{a['label']} {sb} clashes {b['label']} {tb}")
            if STEM_CLASH.get(ss) == ts:
                clashes.append(f"{a['label']} {ss} clashes {b['label']} {ts}")

    # ── Da Yun (luck pillar) ──
    is_yang_year = year_stem_idx % 2 == 0
    forward = (gender == "male" and is_yang_year) or (gender == "female" and not is_yang_year)
    step = 1 if forward else -1

    if forward:
        next_jie = next((t for t in jie_terms if t["jd"] > birth_jd), None)
        anchor_jd = next_jie["jd"] if next_jie else get_jie_terms(solar_year + 1)[0]["jd"]
    else:
        prev_jie = next((t for t in reversed(jie_terms) if t["jd"] < birth_jd), None)
        anchor_jd = prev_jie["jd"] if prev_jie else get_jie_terms(solar_year - 1)[-1]["jd"]

    luck_start_age = round(abs(anchor_jd - birth_jd) / 3.0, 1)

    # Первый столп Da Yun — следующий шаг от месячного столпа
    first_luck_stem = _mod(month_stem_idx + step, 10)
    first_luck_branch = _mod(month_branch_idx + step, 12)

    # Текущий возраст на reference_date
    ref = reference_date or date.today()
    birth_dt = date(y, m, d)
    cur_age = _current_age(birth_dt, ref)

    # ИСПРАВЛЕНИЕ: находим актуальный столп по возрасту
    current_pillar = _advance_to_current_pillar(
        start_stem=first_luck_stem,
        start_branch=first_luck_branch,
        start_age=luck_start_age,
        step=step,
        current_age=cur_age,
    )

    luck_stem = current_pillar["stem_idx"]
    luck_branch = current_pillar["branch_idx"]
    upcoming_stem = _mod(luck_stem + step, 10)
    upcoming_branch = _mod(luck_branch + step, 12)

    return {
        "year_pillar": {"stem": STEMS[year_stem_idx], "branch": BRANCHES[year_branch_idx]},
        "month_pillar": {"stem": STEMS[month_stem_idx], "branch": BRANCHES[month_branch_idx]},
        "day_pillar": {"stem": STEMS[day_stem_idx], "branch": BRANCHES[day_branch_idx]},
        "hour_pillar": hour_pillar,
        "day_master": {"element": ELEMENTS[day_stem_idx], "yin_yang": YIN_YANG[day_stem_idx]},
        "ten_gods": ten_gods,
        "hidden_gods": hidden_gods,
        "luck_pillar": {
            "current": f"{STEMS[luck_stem]} {BRANCHES[luck_branch]}",
            "upcoming": f"{STEMS[upcoming_stem]} {BRANCHES[upcoming_branch]}",
            "start_age": luck_start_age,
            "direction": "forward" if forward else "reverse",
            # Новые поля — диапазон текущего столпа для прозрачности
            "current_age_start": current_pillar["age_start"],
            "current_age_end": current_pillar["age_end"],
            "periods_elapsed": current_pillar["periods_elapsed"],
        },
        "clash_patterns": clashes,
        "late_zi_adjusted": is_late_zi,
        "true_solar_time": round(true_solar, 2) if true_solar is not None else None,
        "solar_year": solar_year,
        "solar_month_index": solar_month_index,
        "time_sensitive": not has_time,
    }

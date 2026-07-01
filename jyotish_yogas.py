"""
Джйотиш — детектор йог.

Принимает:
  planets   — dict из jyotish_calc.sidereal_planet_positions()["planets"]
              ключи: sun, moon, mercury, venus, mars, jupiter, saturn,
                     uranus, neptune, pluto, north_node, south_node,
                     earth, lilith_mean, lilith_true
  asc_sign  — int 0-11 (сидерический знак Лагны), None если время неизвестно

Возвращает список dict:
  {
    "name":           str,   # название йоги
    "present":        bool,  # обнаружена или нет
    "time_sensitive": bool,  # True = требовался асцендент, которого не было
    "planets":        list,  # какие планеты образуют йогу
    "description":    str,   # краткое значение
  }

Проверяются только "классические" йоги — те, что прямо упоминаются
в реляционном, карьерном и тайминг-промптах пайплайна.
"""

# ──────────────────── Справочники ────────────────────

# Владелец знака (0=Овен … 11=Рыбы)
SIGN_LORD: dict[int, str] = {
    0: "mars",    1: "venus",   2: "mercury", 3: "moon",
    4: "sun",     5: "mercury", 6: "venus",   7: "mars",
    8: "jupiter", 9: "saturn",  10: "saturn", 11: "jupiter",
}

# Знак экзальтации планеты
EXALTATION: dict[str, int] = {
    "sun": 0,       # Овен
    "moon": 1,      # Телец
    "mars": 9,      # Козерог
    "mercury": 5,   # Дева
    "jupiter": 3,   # Рак
    "venus": 11,    # Рыбы
    "saturn": 6,    # Весы
}

# Знаки домицилия планеты
OWN_SIGNS: dict[str, list[int]] = {
    "sun":     [4],
    "moon":    [3],
    "mars":    [0, 7],
    "mercury": [2, 5],
    "jupiter": [8, 11],
    "venus":   [1, 6],
    "saturn":  [9, 10],
}

KENDRAS   = {1, 4, 7, 10}
TRIKONAS  = {1, 5, 9}
DUSTHANAS = {6, 8, 12}

# Планеты для большинства йог (без узлов, Земли, транссатурнов, Лилит)
CLASSICAL = {"sun", "moon", "mars", "mercury", "jupiter", "venus", "saturn"}
PANCHA_PLANETS = ["jupiter", "venus", "mars", "mercury", "saturn"]


# ──────────────────── Утилиты ────────────────────

def _sign(planet_key: str, planets: dict) -> int | None:
    p = planets.get(planet_key)
    return p["sign_index"] if p else None


def _house(planet_key: str, planets: dict, asc_sign: int) -> int | None:
    s = _sign(planet_key, planets)
    if s is None:
        return None
    return (s - asc_sign) % 12 + 1


def _same_sign(a: str, b: str, planets: dict) -> bool:
    sa, sb = _sign(a, planets), _sign(b, planets)
    return sa is not None and sb is not None and sa == sb


def _in_kendra_from(planet: str, reference: str, planets: dict) -> bool:
    """Планета в кендре (1,4,7,10) от опорной планеты — без асцендента."""
    sp = _sign(planet, planets)
    sr = _sign(reference, planets)
    if sp is None or sr is None:
        return False
    house_from_ref = (sp - sr) % 12 + 1
    return house_from_ref in KENDRAS


def _exalted_or_own(planet: str, planets: dict) -> bool:
    s = _sign(planet, planets)
    if s is None:
        return False
    return s == EXALTATION.get(planet) or s in OWN_SIGNS.get(planet, [])


def _yoga(name: str, present: bool, planets_involved: list,
          description: str, time_sensitive: bool = False) -> dict:
    return {
        "name": name,
        "present": present,
        "time_sensitive": time_sensitive,
        "planets": planets_involved,
        "description": description,
    }


# ──────────────────── Детекторы ────────────────────

def _budha_aditya(planets):
    present = _same_sign("sun", "mercury", planets)
    return _yoga(
        "Budha-Aditya",
        present,
        ["sun", "mercury"],
        "Солнце + Меркурий в одном знаке: острый интеллект, дар коммуникации, "
        "признание через слово и аналитику.",
    )


def _chandra_mangala(planets):
    present = _same_sign("moon", "mars", planets)
    return _yoga(
        "Chandra-Mangala",
        present,
        ["moon", "mars"],
        "Луна + Марс: сильная воля и эмоциональная интенсивность. "
        "Материальная хватка, способность монетизировать эмоциональные ресурсы.",
    )


def _gajakesari(planets):
    """Юпитер в кендре от Луны — работает без асцендента."""
    present = _in_kendra_from("jupiter", "moon", planets)
    return _yoga(
        "Gajakesari",
        present,
        ["jupiter", "moon"],
        "Юпитер в кендре от Луны: репутация, мудрость, широкое общественное "
        "признание. Одна из самых благоприятных йог.",
    )


def _kemadruma(planets):
    """Луна в изоляции: ни одной классической планеты в соседних знаках."""
    moon_sign = _sign("moon", planets)
    if moon_sign is None:
        return _yoga("Kemadruma", False, ["moon"], "Луна изолирована — эмоциональная уязвимость.")

    adjacent = {(moon_sign - 1) % 12, (moon_sign + 1) % 12}
    neighbors = [
        p for p in CLASSICAL - {"moon"}
        if _sign(p, planets) in adjacent
    ]
    present = len(neighbors) == 0
    return _yoga(
        "Kemadruma",
        present,
        ["moon"],
        "Луна без соседей: эмоциональная изолированность, склонность к одиночеству "
        "или периодам глубокого внутреннего отшельничества.",
    )


def _guru_chandala(planets):
    """Юпитер + Раху в одном знаке — не классическая йога, но часто интерпретируется."""
    rahu_sign = _sign("north_node", planets)
    jup_sign  = _sign("jupiter", planets)
    present   = rahu_sign is not None and jup_sign is not None and rahu_sign == jup_sign
    return _yoga(
        "Guru-Chandala",
        present,
        ["jupiter", "north_node"],
        "Юпитер + Раху: нестандартные убеждения, вызов традиционным системам. "
        "Интуитивная мудрость, но риск догматизма или духовного нарциссизма.",
    )


def _pancha_mahapurusha(planets, asc_sign):
    """Пять Маха-Пуруша йог — требуют Лагны."""
    if asc_sign is None:
        return [_yoga(
            "Pancha Mahapurusha (5 йог)",
            False,
            PANCHA_PLANETS,
            "Требуется время рождения для расчёта Лагны.",
            time_sensitive=True,
        )]

    configs = [
        ("Hamsa",   "jupiter", "Юпитер в домициле/экзальтации в кендре: мудрость, духовность, авторитет."),
        ("Malavya", "venus",   "Венера в домициле/экзальтации в кендре: красота, артистизм, материальный комфорт."),
        ("Ruchaka", "mars",    "Марс в домициле/экзальтации в кендре: лидерство, физическая сила, воля."),
        ("Bhadra",  "mercury", "Меркурий в домициле/экзальтации в кендре: интеллект, красноречие, аналитика."),
        ("Shasha",  "saturn",  "Сатурн в домициле/экзальтации в кендре: дисциплина, власть через терпение."),
    ]
    result = []
    for name, planet, desc in configs:
        h = _house(planet, planets, asc_sign)
        present = h in KENDRAS and _exalted_or_own(planet, planets)
        result.append(_yoga(name, present, [planet], desc))
    return result


def _raja_yoga(planets, asc_sign):
    """Базовая Раджа-йога: лорд кендры + лорд триконы в соединении или в кендре/триконе."""
    if asc_sign is None:
        return [_yoga(
            "Raja Yoga",
            False,
            [],
            "Требуется время рождения для расчёта Лагны.",
            time_sensitive=True,
        )]

    kendra_lords  = {SIGN_LORD[(asc_sign + h - 1) % 12] for h in KENDRAS}
    trikona_lords = {SIGN_LORD[(asc_sign + h - 1) % 12] for h in TRIKONAS}

    found_pairs = []
    for kl in kendra_lords:
        for tl in trikona_lords:
            if kl == tl:
                continue
            if _same_sign(kl, tl, planets):
                found_pairs.append((kl, tl))

    present = len(found_pairs) > 0
    involved = list({p for pair in found_pairs for p in pair})
    return [_yoga(
        "Raja Yoga",
        present,
        involved,
        "Лорд кендры + лорд триконы в соединении: власть, успех, общественное "
        "признание. Сила йоги зависит от знаков и аспектов.",
    )]


def _viparita_raja(planets, asc_sign):
    """Випарита Раджа-йога: лорды 6/8/12 в домах 6/8/12."""
    if asc_sign is None:
        return [_yoga(
            "Viparita Raja Yoga",
            False,
            [],
            "Требуется время рождения.",
            time_sensitive=True,
        )]

    dusthana_lords = {SIGN_LORD[(asc_sign + h - 1) % 12] for h in DUSTHANAS}
    # Все лорды пыльных домов должны быть в пыльных домах
    all_in_dusthana = all(
        _house(lord, planets, asc_sign) in DUSTHANAS
        for lord in dusthana_lords
        if _sign(lord, planets) is not None
    )
    present = len(dusthana_lords) > 1 and all_in_dusthana
    return [_yoga(
        "Viparita Raja Yoga",
        present,
        list(dusthana_lords),
        "Лорды 6/8/12 домов в пыльных домах: трансформация через кризис, "
        "неожиданный подъём из трудностей.",
    )]


def _dhana_yoga(planets, asc_sign):
    """Дхана-йога: лорды 2/11 в соединении с лордами 1/5/9."""
    if asc_sign is None:
        return [_yoga(
            "Dhana Yoga",
            False,
            [],
            "Требуется время рождения.",
            time_sensitive=True,
        )]

    wealth_lords  = {SIGN_LORD[(asc_sign + h - 1) % 12] for h in {2, 11}}
    support_lords = {SIGN_LORD[(asc_sign + h - 1) % 12] for h in {1, 5, 9}}

    found_pairs = []
    for wl in wealth_lords:
        for sl in support_lords:
            if wl != sl and _same_sign(wl, sl, planets):
                found_pairs.append((wl, sl))

    present = len(found_pairs) > 0
    involved = list({p for pair in found_pairs for p in pair})
    return [_yoga(
        "Dhana Yoga",
        present,
        involved,
        "Лорд 2/11 дома + лорд 1/5/9 в соединении: материальное процветание, "
        "накопление богатства через деятельность в соответствии с природой.",
    )]


# ──────────────────── Главная функция ────────────────────

def detect_yogas(planets: dict, asc_sign: int | None = None) -> list[dict]:
    """
    Детектирует все реализованные йоги.
    Возвращает только те, где present=True, плюс все time_sensitive=True
    (чтобы клиент знал что именно не проверялось из-за отсутствия времени).
    """
    yogas: list[dict] = []

    # Независимые от времени
    yogas.append(_budha_aditya(planets))
    yogas.append(_chandra_mangala(planets))
    yogas.append(_gajakesari(planets))
    yogas.append(_kemadruma(planets))
    yogas.append(_guru_chandala(planets))

    # Зависимые от Лагны
    yogas.extend(_pancha_mahapurusha(planets, asc_sign))
    yogas.extend(_raja_yoga(planets, asc_sign))
    yogas.extend(_viparita_raja(planets, asc_sign))
    yogas.extend(_dhana_yoga(planets, asc_sign))

    # Отдаём: найденные + те что не проверялись из-за отсутствия времени
    return [y for y in yogas if y["present"] or y["time_sensitive"]]

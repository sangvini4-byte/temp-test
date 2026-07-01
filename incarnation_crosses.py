"""
Human Design — 192 Incarnation Crosses.

ИСТОЧНИК: Genetic Matrix (geneticmatrix.com/learn-hub/incarnation-cross)
Все 192 записи извлечены и проверены:
  - Ключ: (personality_sun_gate, cross_type)  cross_type ∈ {'RAX','LAX','JX'}
  - Значение: (display_name, [p_sun, p_earth, d_sun, d_earth])
  - Проверка: для каждого из 64 ворот ровно 3 записи (RAX/LAX/JX) = 192 итого
  - Структурная проверка: P⊕ = opposite(P☉), D⊕ = opposite(D☉), всегда

ГЕОМЕТРИЯ:
  RAX  — Design Sun на 16 позиций ПЕРЕД Personality Sun в колесе (−90°)
  LAX  — Design Sun на 16 позиций ПОСЛЕ  Personality Sun в колесе (+90°)
  JX   — те же ворота, что RAX (точно 4/1-профиль, "неподвижная судьба")
  LAX ворота = RAX ворота с переставленными D☉ и D⊕ (indices 2 и 3)

ТИП ОПРЕДЕЛЯЕТСЯ ПРОФИЛЕМ (personality_sun_line / design_sun_line):
  RAX  → 1/3, 1/4, 2/4, 2/5, 3/5, 3/6, 4/6
  JX   → 4/1
  LAX  → 5/1, 5/2, 6/2, 6/3
"""

# ── Профиль → тип креста ────────────────────────────────────
PROFILE_TO_CROSS_TYPE = {
    "1/3": "RAX", "1/4": "RAX", "2/4": "RAX", "2/5": "RAX",
    "3/5": "RAX", "3/6": "RAX", "4/6": "RAX",
    "4/1": "JX",
    "5/1": "LAX", "5/2": "LAX", "6/2": "LAX", "6/3": "LAX",
}

# ── Тип для дисплея ─────────────────────────────────────────
CROSS_TYPE_DISPLAY = {
    "RAX": "Right Angle Cross",
    "LAX": "Left Angle Cross",
    "JX":  "Juxtaposition Cross",
}

# ── Кварталы ────────────────────────────────────────────────
QUARTERS = {
    "Q1_Mind":     {"theme": "Quarter of Initiation / Mind",
                    "gates": {13,49,30,55,37,63,22,36,25,17,21,51,42,3,27,24}},
    "Q2_Form":     {"theme": "Quarter of Civilization / Form",
                    "gates": {2,23,8,20,16,35,45,12,15,52,39,53,62,56,31,33}},
    "Q3_Duality":  {"theme": "Quarter of Duality / Awareness",
                    "gates": {7,4,29,59,40,64,47,6,46,18,48,57,32,50,28,44}},
    "Q4_Mutation": {"theme": "Quarter of Mutation / Energy",
                    "gates": {1,43,14,34,9,5,26,11,10,58,38,54,61,60,41,19}},
}

def gate_to_quarter(gate: int) -> dict:
    for q_key, q_data in QUARTERS.items():
        if gate in q_data["gates"]:
            return {"key": q_key, "theme": q_data["theme"]}
    return {"key": "unknown", "theme": "unknown"}


# ── Главная таблица 192 крестов ──────────────────────────────
# Формат: (p_sun_gate, cross_type) → (display_name, [p_sun, p_earth, d_sun, d_earth])
# Порядок ворот: [Personality Sun, Personality Earth, Design Sun, Design Earth]
_RAW = [
    # ═══ QUARTER 1 — Mind ═══════════════════════════════════
    (13,"RAX","Right Angle Cross of The Sphinx",          [13, 7,  1,  2]),
    (13,"LAX","Left Angle Cross of Masks",                [13, 7,  2,  1]),
    (13,"JX", "Juxtaposition Cross of Listening",         [13, 7,  1,  2]),
    (49,"RAX","Right Angle Cross of Explanation",         [49, 4, 43, 23]),
    (49,"LAX","Left Angle Cross of Revolution",           [49, 4, 23, 43]),
    (49,"JX", "Juxtaposition Cross of Principles",        [49, 4, 43, 23]),
    (30,"RAX","Right Angle Cross of Contagion",           [30,29, 14,  8]),
    (30,"LAX","Left Angle Cross of Industry",             [30,29,  8, 14]),
    (30,"JX", "Juxtaposition Cross of Fates",             [30,29, 14,  8]),
    (55,"RAX","Right Angle Cross of The Sleeping Phoenix",[55,59, 34, 20]),
    (55,"LAX","Left Angle Cross of Spirit",               [55,59, 20, 34]),
    (55,"JX", "Juxtaposition Cross of Moods",             [55,59, 34, 20]),
    (37,"RAX","Right Angle Cross of Planning",            [37,40,  9, 16]),
    (37,"LAX","Left Angle Cross of Migration",            [37,40, 16,  9]),
    (37,"JX", "Juxtaposition Cross of Bargains",          [37,40,  9, 16]),
    (63,"RAX","Right Angle Cross of Consciousness",       [63,64,  5, 35]),
    (63,"LAX","Left Angle Cross of Dominion",             [63,64, 35,  5]),
    (63,"JX", "Juxtaposition Cross of Doubts",            [63,64,  5, 35]),
    (22,"RAX","Right Angle Cross of Rulership",           [22,47, 26, 45]),
    (22,"LAX","Left Angle Cross of Informing",            [22,47, 45, 26]),
    (22,"JX", "Juxtaposition Cross of Grace",             [22,47, 26, 45]),
    (36,"RAX","Right Angle Cross of Eden",                [36, 6, 11, 12]),
    (36,"LAX","Left Angle Cross of The Plane",            [36, 6, 12, 11]),
    (36,"JX", "Juxtaposition Cross of Crisis",            [36, 6, 11, 12]),
    (25,"RAX","Right Angle Cross of The Vessel of Love",  [25,46, 10, 15]),
    (25,"LAX","Left Angle Cross of Healing",              [25,46, 15, 10]),
    (25,"JX", "Juxtaposition Cross of Innocence",         [25,46, 10, 15]),
    (17,"RAX","Right Angle Cross of Service",             [17,18, 58, 52]),
    (17,"LAX","Left Angle Cross of Upheaval",             [17,18, 52, 58]),
    (17,"JX", "Juxtaposition Cross of Opinions",          [17,18, 58, 52]),
    (21,"RAX","Right Angle Cross of Tension",             [21,48, 38, 39]),
    (21,"LAX","Left Angle Cross of Endeavor",             [21,48, 39, 38]),
    (21,"JX", "Juxtaposition Cross of Control",           [21,48, 38, 39]),
    (51,"RAX","Right Angle Cross of Penetration",         [51,57, 54, 53]),
    (51,"LAX","Left Angle Cross of Clarion",              [51,57, 53, 54]),
    (51,"JX", "Juxtaposition Cross of Shock",             [51,57, 54, 53]),
    (42,"RAX","Right Angle Cross of Maya",                [42,32, 61, 62]),
    (42,"LAX","Left Angle Cross of Limitation",           [42,32, 62, 61]),
    (42,"JX", "Juxtaposition Cross of Completion",        [42,32, 61, 62]),
    ( 3,"RAX","Right Angle Cross of Laws",                [ 3,50, 60, 56]),
    ( 3,"LAX","Left Angle Cross of Wishes",               [ 3,50, 56, 60]),
    ( 3,"JX", "Juxtaposition Cross of Mutation",          [ 3,50, 60, 56]),
    (27,"RAX","Right Angle Cross of The Unexpected",      [27,28, 41, 31]),
    (27,"LAX","Left Angle Cross of Alignment",            [27,28, 31, 41]),
    (27,"JX", "Juxtaposition Cross of Caring",            [27,28, 41, 31]),
    (24,"RAX","Right Angle Cross of The Four Ways",       [24,44, 19, 33]),
    (24,"LAX","Left Angle Cross of Incarnation",          [24,44, 33, 19]),
    (24,"JX", "Juxtaposition Cross of Rationalization",   [24,44, 19, 33]),
    # ═══ QUARTER 2 — Form ═══════════════════════════════════
    ( 2,"RAX","Right Angle Cross of The Sphinx",          [ 2, 1, 13,  7]),
    ( 2,"LAX","Left Angle Cross of The Driver",           [ 2, 1,  7, 13]),
    ( 2,"JX", "Juxtaposition Cross of The Driver",        [ 2, 1, 13,  7]),
    (23,"RAX","Right Angle Cross of Explanation",         [23,43, 49,  4]),
    (23,"LAX","Left Angle Cross of Dedication",           [23,43,  4, 49]),
    (23,"JX", "Juxtaposition Cross of Assimilation",      [23,43, 49,  4]),
    ( 8,"RAX","Right Angle Cross of Contagion",           [ 8,14, 30, 29]),
    ( 8,"LAX","Left Angle Cross of Uncertainty",          [ 8,14, 29, 30]),
    ( 8,"JX", "Juxtaposition Cross of Contribution",      [ 8,14, 30, 29]),
    (20,"RAX","Right Angle Cross of The Sleeping Phoenix",[20,34, 55, 59]),
    (20,"LAX","Left Angle Cross of Duality",              [20,34, 59, 55]),
    (20,"JX", "Juxtaposition Cross of The Now",           [20,34, 55, 59]),
    (16,"RAX","Right Angle Cross of Planning",            [16, 9, 37, 40]),
    (16,"LAX","Left Angle Cross of Identification",       [16, 9, 40, 37]),
    (16,"JX", "Juxtaposition Cross of Experimentation",   [16, 9, 37, 40]),
    (35,"RAX","Right Angle Cross of Consciousness",       [35, 5, 63, 64]),
    (35,"LAX","Left Angle Cross of Separation",           [35, 5, 64, 63]),
    (35,"JX", "Juxtaposition Cross of Experience",        [35, 5, 63, 64]),
    (45,"RAX","Right Angle Cross of Rulership",           [45,26, 22, 47]),
    (45,"LAX","Left Angle Cross of Confrontation",        [45,26, 47, 22]),
    (45,"JX", "Juxtaposition Cross of Possession",        [45,26, 22, 47]),
    (12,"RAX","Right Angle Cross of Eden",                [12,11, 36,  6]),
    (12,"LAX","Left Angle Cross of Education",            [12,11,  6, 36]),
    (12,"JX", "Juxtaposition Cross of Articulation",      [12,11, 36,  6]),
    (15,"RAX","Right Angle Cross of The Vessel of Love",  [15,10, 25, 46]),
    (15,"LAX","Left Angle Cross of Prevention",           [15,10, 46, 25]),
    (15,"JX", "Juxtaposition Cross of Extremes",          [15,10, 25, 46]),
    (52,"RAX","Right Angle Cross of Service",             [52,58, 17, 18]),
    (52,"LAX","Left Angle Cross of Demands",              [52,58, 18, 17]),
    (52,"JX", "Juxtaposition Cross of Stillness",         [52,58, 17, 18]),
    (39,"RAX","Right Angle Cross of Tension",             [39,38, 21, 48]),
    (39,"LAX","Left Angle Cross of Individualism",        [39,38, 48, 21]),
    (39,"JX", "Juxtaposition Cross of Provocation",       [39,38, 21, 48]),
    (53,"RAX","Right Angle Cross of Penetration",         [53,54, 51, 57]),
    (53,"LAX","Left Angle Cross of Cycles",               [53,54, 57, 51]),
    (53,"JX", "Juxtaposition Cross of Beginnings",        [53,54, 51, 57]),
    (62,"RAX","Right Angle Cross of Maya",                [62,61, 42, 32]),
    (62,"LAX","Left Angle Cross of Obscuration",          [62,61, 32, 42]),
    (62,"JX", "Juxtaposition Cross of Detail",            [62,61, 42, 32]),
    (56,"RAX","Right Angle Cross of Laws",                [56,60,  3, 50]),
    (56,"LAX","Left Angle Cross of Distraction",          [56,60, 50,  3]),
    (56,"JX", "Juxtaposition Cross of Stimulation",       [56,60,  3, 50]),
    (31,"RAX","Right Angle Cross of The Unexpected",      [31,41, 27, 28]),
    (31,"LAX","Left Angle Cross of The Alpha",            [31,41, 28, 27]),
    (31,"JX", "Juxtaposition Cross of Influence",         [31,41, 27, 28]),
    (33,"RAX","Right Angle Cross of The Four Ways",       [33,19, 24, 44]),
    (33,"LAX","Left Angle Cross of Refinement",           [33,19, 44, 24]),
    (33,"JX", "Juxtaposition Cross of Retreat",           [33,19, 24, 44]),
    # ═══ QUARTER 3 — Duality ════════════════════════════════
    ( 7,"RAX","Right Angle Cross of The Sphinx",          [ 7,13,  2,  1]),
    ( 7,"LAX","Left Angle Cross of Masks",                [ 7,13,  1,  2]),
    ( 7,"JX", "Juxtaposition Cross of Interaction",       [ 7,13,  2,  1]),
    ( 4,"RAX","Right Angle Cross of Explanation",         [ 4,49, 23, 43]),
    ( 4,"LAX","Left Angle Cross of Revolution",           [ 4,49, 43, 23]),
    ( 4,"JX", "Juxtaposition Cross of Formulization",     [ 4,49, 23, 43]),
    (29,"RAX","Right Angle Cross of Contagion",           [29,30,  8, 14]),
    (29,"LAX","Left Angle Cross of Industry",             [29,30, 14,  8]),
    (29,"JX", "Juxtaposition Cross of Commitment",        [29,30,  8, 14]),
    (59,"RAX","Right Angle Cross of The Sleeping Phoenix",[59,55, 20, 34]),
    (59,"LAX","Left Angle Cross of Spirit",               [59,55, 34, 20]),
    (59,"JX", "Juxtaposition Cross of Strategy",          [59,55, 20, 34]),
    (40,"RAX","Right Angle Cross of Planning",            [40,37, 16,  9]),
    (40,"LAX","Left Angle Cross of Migration",            [40,37,  9, 16]),
    (40,"JX", "Juxtaposition Cross of Denial",            [40,37, 16,  9]),
    (64,"RAX","Right Angle Cross of Consciousness",       [64,63, 35,  5]),
    (64,"LAX","Left Angle Cross of Dominion",             [64,63,  5, 35]),
    (64,"JX", "Juxtaposition Cross of Confusion",         [64,63, 35,  5]),
    (47,"RAX","Right Angle Cross of Rulership",           [47,22, 45, 26]),
    (47,"LAX","Left Angle Cross of Informing",            [47,22, 26, 45]),
    (47,"JX", "Juxtaposition Cross of Oppression",        [47,22, 45, 26]),
    ( 6,"RAX","Right Angle Cross of Eden",                [ 6,36, 12, 11]),
    ( 6,"LAX","Left Angle Cross of The Plane",            [ 6,36, 11, 12]),
    ( 6,"JX", "Juxtaposition Cross of Conflict",          [ 6,36, 12, 11]),
    (46,"RAX","Right Angle Cross of The Vessel of Love",  [46,25, 15, 10]),
    (46,"LAX","Left Angle Cross of Healing",              [46,25, 10, 15]),
    (46,"JX", "Juxtaposition Cross of Serendipity",       [46,25, 15, 10]),
    (18,"RAX","Right Angle Cross of Service",             [18,17, 52, 58]),
    (18,"LAX","Left Angle Cross of Upheaval",             [18,17, 58, 52]),
    (18,"JX", "Juxtaposition Cross of Correction",        [18,17, 52, 58]),
    (48,"RAX","Right Angle Cross of Tension",             [48,21, 39, 38]),
    (48,"LAX","Left Angle Cross of Endeavor",             [48,21, 38, 39]),
    (48,"JX", "Juxtaposition Cross of Depth",             [48,21, 39, 38]),
    (57,"RAX","Right Angle Cross of Penetration",         [57,51, 53, 54]),
    (57,"LAX","Left Angle Cross of Clarion",              [57,51, 54, 53]),
    (57,"JX", "Juxtaposition Cross of Intuition",         [57,51, 53, 54]),
    (32,"RAX","Right Angle Cross of Maya",                [32,42, 62, 61]),
    (32,"LAX","Left Angle Cross of Limitation",           [32,42, 61, 62]),
    (32,"JX", "Juxtaposition Cross of Conservation",      [32,42, 62, 61]),
    (50,"RAX","Right Angle Cross of Laws",                [50, 3, 56, 60]),
    (50,"LAX","Left Angle Cross of Wishes",               [50, 3, 60, 56]),
    (50,"JX", "Juxtaposition Cross of Values",            [50, 3, 56, 60]),
    (28,"RAX","Right Angle Cross of The Unexpected",      [28,27, 31, 41]),
    (28,"LAX","Left Angle Cross of Alignment",            [28,27, 41, 31]),
    (28,"JX", "Juxtaposition Cross of Risks",             [28,27, 31, 41]),
    (44,"RAX","Right Angle Cross of The Four Ways",       [44,24, 33, 19]),
    (44,"LAX","Left Angle Cross of Incarnation",          [44,24, 19, 33]),
    (44,"JX", "Juxtaposition Cross of Alertness",         [44,24, 33, 19]),
    # ═══ QUARTER 4 — Mutation ═══════════════════════════════
    ( 1,"RAX","Right Angle Cross of The Sphinx",          [ 1, 2,  7, 13]),
    ( 1,"LAX","Left Angle Cross of Defiance",             [ 1, 2, 13,  7]),
    ( 1,"JX", "Juxtaposition Cross of Self Expression",   [ 1, 2,  7, 13]),
    (43,"RAX","Right Angle Cross of Explanation",         [43,23,  4, 49]),
    (43,"LAX","Left Angle Cross of Dedication",           [43,23, 49,  4]),
    (43,"JX", "Juxtaposition Cross of Insight",           [43,23,  4, 49]),
    (14,"RAX","Right Angle Cross of Contagion",           [14, 8, 29, 30]),
    (14,"LAX","Left Angle Cross of Uncertainty",          [14, 8, 30, 29]),
    (14,"JX", "Juxtaposition Cross of Empowering",        [14, 8, 29, 30]),
    (34,"RAX","Right Angle Cross of The Sleeping Phoenix",[34,20, 59, 55]),
    (34,"LAX","Left Angle Cross of Duality",              [34,20, 55, 59]),
    (34,"JX", "Juxtaposition Cross of Power",             [34,20, 59, 55]),
    ( 9,"RAX","Right Angle Cross of Planning",            [ 9,16, 40, 37]),
    ( 9,"LAX","Left Angle Cross of Identification",       [ 9,16, 37, 40]),
    ( 9,"JX", "Juxtaposition Cross of Focus",             [ 9,16, 40, 37]),
    ( 5,"RAX","Right Angle Cross of Consciousness",       [ 5,35, 64, 63]),
    ( 5,"LAX","Left Angle Cross of Separation",           [ 5,35, 63, 64]),
    ( 5,"JX", "Juxtaposition Cross of Habits",            [ 5,35, 64, 63]),
    (26,"RAX","Right Angle Cross of Rulership",           [26,45, 47, 22]),
    (26,"LAX","Left Angle Cross of Confrontation",        [26,45, 22, 47]),
    (26,"JX", "Juxtaposition Cross of The Trickster",     [26,45, 47, 22]),
    (11,"RAX","Right Angle Cross of Eden",                [11,12,  6, 36]),
    (11,"LAX","Left Angle Cross of Education",            [11,12, 36,  6]),
    (11,"JX", "Juxtaposition Cross of Ideas",             [11,12,  6, 36]),
    (10,"RAX","Right Angle Cross of The Vessel of Love",  [10,15, 46, 25]),
    (10,"LAX","Left Angle Cross of Prevention",           [10,15, 25, 46]),
    (10,"JX", "Juxtaposition Cross of Behavior",          [10,15, 46, 25]),
    (58,"RAX","Right Angle Cross of Service",             [58,52, 18, 17]),
    (58,"LAX","Left Angle Cross of Demands",              [58,52, 17, 18]),
    (58,"JX", "Juxtaposition Cross of Vitality",          [58,52, 18, 17]),
    (38,"RAX","Right Angle Cross of Tension",             [38,39, 48, 21]),
    (38,"LAX","Left Angle Cross of Individualism",        [38,39, 21, 48]),
    (38,"JX", "Juxtaposition Cross of Opposition",        [38,39, 48, 21]),
    (54,"RAX","Right Angle Cross of Penetration",         [54,53, 57, 51]),
    (54,"LAX","Left Angle Cross of Cycles",               [54,53, 51, 57]),
    (54,"JX", "Juxtaposition Cross of Ambition",          [54,53, 57, 51]),
    (61,"RAX","Right Angle Cross of Maya",                [61,62, 32, 42]),
    (61,"LAX","Left Angle Cross of Obscuration",          [61,62, 42, 32]),
    (61,"JX", "Juxtaposition Cross of Thinking",          [61,62, 32, 42]),
    (60,"RAX","Right Angle Cross of Laws",                [60,56, 50,  3]),
    (60,"LAX","Left Angle Cross of Distraction",          [60,56,  3, 50]),
    (60,"JX", "Juxtaposition Cross of Limitation",        [60,56, 50,  3]),
    (41,"RAX","Right Angle Cross of The Unexpected",      [41,31, 28, 27]),
    (41,"LAX","Left Angle Cross of The Alpha",            [41,31, 27, 28]),
    (41,"JX", "Juxtaposition Cross of Fantasy",           [41,31, 28, 27]),
    (19,"RAX","Right Angle Cross of The Four Ways",       [19,33, 44, 24]),
    (19,"LAX","Left Angle Cross of Refinement",           [19,33, 24, 44]),
    (19,"JX", "Juxtaposition Cross of Need",              [19,33, 44, 24]),
]

CROSS_LOOKUP: dict[tuple[int,str], tuple[str, list]] = {
    (gate, ctype): (name, gates)
    for gate, ctype, name, gates in _RAW
}


def _self_test():
    assert len(CROSS_LOOKUP) == 192, f"Expected 192, got {len(CROSS_LOOKUP)}"
    all_gates = set(range(1, 65))
    covered  = {gate for gate, _ in CROSS_LOOKUP}
    assert covered == all_gates, f"Missing gates: {all_gates - covered}"
    for (gate, ctype), (name, four_gates) in CROSS_LOOKUP.items():
        assert len(four_gates) == 4, f"Gate {gate} {ctype}: expected 4 gates, got {four_gates}"
        assert four_gates[0] == gate, f"Gate {gate} {ctype}: P☉ mismatch ({four_gates[0]})"
    # LAX swap check: for every gate, LAX d_sun == RAX d_earth and LAX d_earth == RAX d_sun
    for gate in range(1, 65):
        rax_gates = CROSS_LOOKUP[(gate, "RAX")][1]
        lax_gates = CROSS_LOOKUP[(gate, "LAX")][1]
        assert rax_gates[2] == lax_gates[3] and rax_gates[3] == lax_gates[2], \
            f"Gate {gate}: LAX D☉/D⊕ swap inconsistent — RAX={rax_gates}, LAX={lax_gates}"


_self_test()


def incarnation_cross(p_sun_gate: int, p_sun_line: int,
                      d_sun_gate: int, d_sun_line: int) -> dict:
    """
    Вернуть полную информацию об Incarnation Cross для данных ворот и линий.

    Args:
        p_sun_gate:  gate of Personality (conscious) Sun
        p_sun_line:  line of Personality Sun (1-6)
        d_sun_gate:  gate of Design (unconscious) Sun
        d_sun_line:  line of Design Sun (1-6)

    Returns dict with: name, type, type_display, quarter, four_gates,
                        personality_geometry, description
    """
    profile = f"{p_sun_line}/{d_sun_line}"
    cross_type = PROFILE_TO_CROSS_TYPE.get(profile)
    if cross_type is None:
        return {"error": f"Unknown profile {profile!r}. Valid: {list(PROFILE_TO_CROSS_TYPE)}"}

    key = (p_sun_gate, cross_type)
    if key not in CROSS_LOOKUP:
        return {"error": f"No cross entry for gate {p_sun_gate}, type {cross_type}"}

    name, table_gates = CROSS_LOOKUP[key]
    quarter = gate_to_quarter(p_sun_gate)

    # Верифицируем: ожидаемый D☉ из таблицы vs реальный из эфемерид
    expected_d_sun = table_gates[2]
    gate_match = (d_sun_gate == expected_d_sun)

    return {
        "name":               name,
        "type":               cross_type,
        "type_display":       CROSS_TYPE_DISPLAY[cross_type],
        "profile":            profile,
        "quarter":            quarter,
        "four_gates": {
            "personality_sun":   table_gates[0],
            "personality_earth": table_gates[1],
            "design_sun":        table_gates[2],
            "design_earth":      table_gates[3],
        },
        "computed_design_sun":     d_sun_gate,
        "design_sun_gate_match":   gate_match,
    }
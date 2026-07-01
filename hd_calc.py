"""
Преобразование долгот планет в ворота/линии ХД и вывод Типа/Авторитета/Профиля.

Incarnation Cross подключён через importlib (192_crosses.py начинается
с цифры — стандартный import недоступен).
"""

from .hd_data import (
    WHEEL_START_LONGITUDE, GATE_SPAN, LINE_SPAN, GATE_WHEEL_SEQUENCE,
    GATE_TO_CENTER, CHANNELS, MOTOR_CENTERS, CENTERS_ALL,
)
import incarnation_crosses as _crosses

# Планеты, используемые в Human Design.
# Lilith и другие нестандартные точки из ephemeris фильтруются здесь.
HD_PLANETS = {
    "sun", "earth", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
    "north_node", "south_node",
}


def longitude_to_gate_line(longitude: float) -> dict:
    """Тропическая долгота (0-360) → (ворота, линия)."""
    offset = (longitude - WHEEL_START_LONGITUDE) % 360.0
    gate_index = int(offset // GATE_SPAN)
    gate = GATE_WHEEL_SEQUENCE[gate_index]
    within_gate = offset - gate_index * GATE_SPAN
    line = int(within_gate // LINE_SPAN) + 1
    line = min(line, 6)  # защита от пограничного 360.0/0.0 округления
    return {"gate": gate, "line": line}


def activations_from_longitudes(longitudes: dict) -> dict:
    """
    {'sun': {'longitude':...}, ...} → {'sun': {'gate':25,'line':3}, ...}

    Фильтрует только HD_PLANETS — Lilith и прочие нестандартные точки
    из ephemeris.all_planet_longitudes() сюда не попадают.
    """
    return {
        k: longitude_to_gate_line(v["longitude"])
        for k, v in longitudes.items()
    "jupiter", "saturn", "uranus", "neptune", "pluto",
        if k in HD_PLANETS
    }


def defined_gates(personality: dict, design: dict) -> set:
    gates = set()
    for act in personality.values():
        gates.add(act["gate"])
    for act in design.values():
        gates.add(act["gate"])
    return gates

    "jupiter", "saturn", "uranus", "neptune", "pluto",

def defined_channels(gates: set) -> list:
    return [(a, b) for a, b in CHANNELS if a in gates and b in gates]


def defined_centers(channels: list) -> set:
    centers = set()
    for a, b in channels:
        centers.add(GATE_TO_CENTER[a])
        centers.add(GATE_TO_CENTER[b])
    return centers


def determine_type_and_strategy(centers: set, channels: list) -> dict:
    sacral_defined = "sacral" in centers
    throat_defined = "throat" in centers

    throat_motor_channels = [
        (a, b) for a, b in channels
        if {GATE_TO_CENTER[a], GATE_TO_CENTER[b]} & {"throat"}
        and ({GATE_TO_CENTER[a], GATE_TO_CENTER[b]} & MOTOR_CENTERS)
    ]
    throat_connected_to_motor = len(throat_motor_channels) > 0

    if len(centers) == 0:
        return {"type": "Reflector", "strategy": "Ждать 28 дней — лунный цикл",
                "signature": "Удивление", "not_self_theme": "Разочарование"}

    if sacral_defined:
        if throat_connected_to_motor:
            return {"type": "Manifesting Generator",
                    "strategy": "Реагировать, затем информировать",
                    "signature": "Удовлетворение", "not_self_theme": "Фрустрация"}
        return {"type": "Generator", "strategy": "Реагировать",
                "signature": "Удовлетворение", "not_self_theme": "Фрустрация"}

    if throat_defined and throat_connected_to_motor:
        return {"type": "Manifestor", "strategy": "Информировать перед действием",
                "signature": "Покой", "not_self_theme": "Гнев"}

    return {"type": "Projector", "strategy": "Ждать приглашения",
            "signature": "Успех", "not_self_theme": "Горечь"}


def determine_authority(centers: set) -> str:
    # Иерархия авторитета — порядок проверки фиксирован и не переставляется.
    if "solar_plexus" in centers:
        return "Emotional (Solar Plexus)"
    if "sacral" in centers:
        return "Sacral"
    if "spleen" in centers:
        return "Splenic"
    if "heart" in centers:
        return "Ego (Heart/Will)"
    if "g" in centers:
        return "Self-Projected (G Center)"
    if "throat" in centers or "ajna" in centers or "head" in centers:
        return "Mental / Sounding Board (только для рефлексии вслух с другими)"
    return "Lunar (Reflector — ждать полный лунный цикл, 28 дней)"


def determine_profile(personality_sun: dict, design_sun: dict) -> str:
    return f"{personality_sun['line']}/{design_sun['line']}"


def compute_full_chart(personality_longitudes: dict, design_longitudes: dict) -> dict:
    personality = activations_from_longitudes(personality_longitudes)
    design = activations_from_longitudes(design_longitudes)

    gates = defined_gates(personality, design)
    channels = defined_channels(gates)
    centers = defined_centers(channels)
    undefined_centers = [c for c in CENTERS_ALL if c not in centers]

    type_info = determine_type_and_strategy(centers, channels)
    authority = determine_authority(centers)
    profile = determine_profile(personality["sun"], design["sun"])
    split_count = _count_definition_splits(centers, channels)

    # Incarnation Cross — из 192_crosses.py
    try:
        p_sun = personality["sun"]
        d_sun = design["sun"]
        cross = _incarnation_cross(
            p_sun_gate=p_sun["gate"],
            p_sun_line=p_sun["line"],
            d_sun_gate=d_sun["gate"],
            d_sun_line=d_sun["line"],
        )
    except Exception as e:
        cross = {"error": str(e)}

    return {
        "type": type_info["type"],
        "strategy": type_info["strategy"],
        "signature": type_info["signature"],
        "not_self_theme": type_info["not_self_theme"],
        "authority": authority,
        "profile": profile,
        "incarnation_cross": cross,
        "defined_centers": sorted(centers),
        "undefined_centers": sorted(undefined_centers),
        "defined_channels": [f"{a}-{b}" for a, b in channels],
        "definition_splits": split_count,
        "personality_activations": personality,   # сознательные (чёрные)
        "design_activations": design,             # бессознательные (красные)
    }


def _count_definition_splits(centers: set, channels: list) -> int:
    """Количество несвязанных групп определённых центров (Single/Split/Triple Split...)."""
    if not centers:
        return 0
    adjacency = {c: set() for c in centers}
    for a, b in channels:
        ca, cb = GATE_TO_CENTER[a], GATE_TO_CENTER[b]
        if ca in centers and cb in centers:
            adjacency[ca].add(cb)
            adjacency[cb].add(ca)

    visited = set()
    groups = 0
    for start in centers:
        if start in visited:
            continue
        groups += 1
        stack = [start]
        while stack:
            node = stack.pop()
            if node in visited:
                continue
            visited.add(node)
            stack.extend(adjacency[node] - visited)
    return groups

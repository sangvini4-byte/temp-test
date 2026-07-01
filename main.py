"""
Astrology micro-service — Swiss Ephemeris внутри Docker-сети.

Эндпоинты:
  GET  /health          — для docker healthcheck
  POST /jyotish         — сидерические позиции + накшатры + даша + йоги
  POST /western         — тропические позиции + аспекты + дома + доминанты
  POST /human-design    — ворота/линии/центры/тип/авторитет/профиль + крест
  POST /bazi            — четыре столпа + Десять Богов + Да Юнь
"""
import importlib
from datetime import datetime
from typing import Optional, Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from . ephemeris as eph
from . jyotish_calc as jc
from . jyotish_yogas as jy
from . hd_calc
from . bazi_calc

# 192_crosses.py начинается с цифры — стандартный import недоступен.
# hd_calc уже загружает его сам; здесь импорт не нужен.

app = FastAPI(title="Blueprint Astrology Service")


# ────────────────────────── Models ──────────────────────────

class BirthInput(BaseModel):
    birth_date: str = Field(..., description="YYYY-MM-DD")
    birth_time: Optional[str] = Field(
        None, description="HH:MM локальное. None или 'UNKNOWN' если неизвестно"
    )
    timezone: float = Field(..., description="UTC offset в часах, напр. 3 или -5.5")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    gender: Optional[Literal["male", "female"]] = Field(
        None, description="Нужен только для /bazi (направление Да Юнь)"
    )


# ────────────────────────── Helpers ──────────────────────────

def _parse_birth(inp: BirthInput) -> tuple[float, bool]:
    """Возвращает (jd_ut, has_time)."""
    try:
        y, m, d = (int(x) for x in inp.birth_date.split("-"))
    except Exception:
        raise HTTPException(
            400, f"birth_date должен быть YYYY-MM-DD, получено: {inp.birth_date}"
        )

    has_time = bool(inp.birth_time) and inp.birth_time.upper() != "UNKNOWN"
    if has_time:
        try:
            hh, mm = (int(x) for x in inp.birth_time.split(":"))
        except Exception:
            raise HTTPException(
                400, f"birth_time должен быть HH:MM, получено: {inp.birth_time}"
            )
        hour_decimal = hh + mm / 60.0
    else:
        hour_decimal = 12.0

    jd_ut = eph.to_jd_ut(y, m, d, hour_decimal, inp.timezone)
    return jd_ut, has_time


# Таблица аспектов: угол → (название, орб)
_MAJOR_ASPECTS: dict[int, tuple[str, float]] = {
    0:   ("conjunction",  8.0),
    60:  ("sextile",      6.0),
    90:  ("square",       8.0),
    120: ("trine",        8.0),
    180: ("opposition",   8.0),
}

_ASPECT_PLANETS = {
    "sun", "moon", "mercury", "venus", "mars",
    "jupiter", "saturn", "uranus", "neptune", "pluto",
}


def _compute_aspects(planets: dict) -> list[dict]:
    keys = [k for k in planets if k in _ASPECT_PLANETS]
    aspects = []
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            diff = abs(planets[a]["longitude"] - planets[b]["longitude"]) % 360
            if diff > 180:
                diff = 360 - diff
            for angle, (name, orb) in _MAJOR_ASPECTS.items():
                deviation = abs(diff - angle)
                if deviation <= orb:
                    aspects.append({
                        "planet_a": a,
                        "planet_b": b,
                        "aspect": name,
                        "orb": round(deviation, 2),
                        "angle": round(diff, 2),
                    })
                    break
    return aspects


def _dominant_element_modality(planets: dict) -> dict:
    elements   = ["Fire", "Earth", "Air", "Water"]
    modalities = ["Cardinal", "Fixed", "Mutable"]
    elem_count = {e: 0 for e in elements}
    mod_count  = {m: 0 for m in modalities}

    for k, v in planets.items():
        if k not in _ASPECT_PLANETS:
            continue
        sign_idx = int(v["longitude"] // 30) % 12
        elem_count[elements[sign_idx % 4]] += 1
        mod_count[modalities[sign_idx % 3]] += 1

    return {
        "elements":          elem_count,
        "modalities":        mod_count,
        "dominant_element":  max(elem_count, key=elem_count.get),
        "dominant_modality": max(mod_count,  key=mod_count.get),
    }


# ────────────────────────── Routes ──────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "ephe_mode": eph.EPHE_MODE}


@app.post("/jyotish")
def jyotish(inp: BirthInput):
    jd_ut, has_time = _parse_birth(inp)

    positions = jc.sidereal_planet_positions(jd_ut)

    ascendant = None
    if has_time:
        if inp.latitude is None or inp.longitude is None:
            raise HTTPException(
                400, "latitude/longitude обязательны, когда birth_time известен"
            )
        ascendant = jc.ascendant_sidereal(jd_ut, inp.latitude, inp.longitude)

    moon_sid_lon  = positions["planets"]["moon"]["longitude"]
    birth_date_obj = datetime.strptime(inp.birth_date, "%Y-%m-%d").date()
    dasha = jc.vimshottari_dasha(moon_sid_lon, birth_date_obj)

    asc_sign = ascendant["sign_index"] if ascendant else None
    yogas    = jy.detect_yogas(positions["planets"], asc_sign)

    return {
        "time_sensitive": not has_time,
        "ayanamsha":      positions["ayanamsha"],
        "planets":        positions["planets"],
        "ascendant":      ascendant,
        "dasha":          dasha,
        "yogas":          yogas,
    }


@app.post("/western")
def western(inp: BirthInput):
    jd_ut, has_time = _parse_birth(inp)
    tropical = eph.all_planet_longitudes(jd_ut)

    ascendant = None
    houses    = None
    if has_time:
        if inp.latitude is None or inp.longitude is None:
            raise HTTPException(
                400, "latitude/longitude обязательны, когда birth_time известен"
            )
        import swisseph as swe
        cusps, ascmc = swe.houses_ex(jd_ut, inp.latitude, inp.longitude, b"P")
        ascendant = {
            "longitude":      round(ascmc[0], 4),
            "sign_index":     int(ascmc[0] // 30),
            "degree_in_sign": round(ascmc[0] % 30, 4),
        }
        houses = [round(c, 4) for c in cusps]

    planets = {
        k: {
            "longitude":      round(v["longitude"], 4),
            "sign_index":     int(v["longitude"] // 30),
            "degree_in_sign": round(v["longitude"] % 30, 4),
            "retrograde":     v["retrograde"],
            # Номер дома — только если известна Лагна
            "house": (
                (int(v["longitude"] // 30) - int(ascendant["longitude"] // 30)) % 12 + 1
                if ascendant else None
            ),
        }
        for k, v in tropical.items()
    }

    aspects = _compute_aspects(planets)
    pattern = _dominant_element_modality(planets)

    return {
        "time_sensitive":  not has_time,
        "planets":         planets,
        "ascendant":       ascendant,
        "house_cusps":     houses,
        "aspects":         aspects,
        "dominant_pattern": pattern,
    }


@app.post("/human-design")
def human_design(inp: BirthInput):
    jd_ut, has_time = _parse_birth(inp)
    if not has_time:
        raise HTTPException(
            400,
            "Human Design требует точное время рождения — без него ворота "
            "и линии будут смещены на непредсказуемую величину.",
        )

    personality_longitudes = eph.all_planet_longitudes(jd_ut)
    design_jd              = eph.find_design_jd(jd_ut)
    design_longitudes      = eph.all_planet_longitudes(design_jd)

    chart = hd_calc.compute_full_chart(personality_longitudes, design_longitudes)
    chart["design_date_ut"] = design_jd
    return chart


@app.post("/bazi")
def bazi(inp: BirthInput):
    if inp.gender is None:
        raise HTTPException(
            400,
            "Поле gender ('male' или 'female') обязательно для /bazi — "
            "от него зависит направление Да Юнь.",
        )
    if inp.longitude is None:
        raise HTTPException(
            400,
            "Поле longitude обязательно для /bazi — нужно для true solar time.",
        )
    try:
        result = bazi_calc.compute_bazi(
            birth_date=inp.birth_date,
            birth_time=inp.birth_time,
            tz_offset=inp.timezone,
            longitude=inp.longitude,
            gender=inp.gender,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))

    return result

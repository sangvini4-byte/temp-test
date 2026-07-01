// ══════════════════════════════════════════════════════════════
//  n8n Code Node — "Astrology Service: все эндпоинты"
//  Ставится ПОСЛЕ "Extract Geocode" ноды.
//
//  Вызывает все четыре эндпоинта Python-сервиса:
//    /jyotish       — всегда
//    /western       — всегда
//    /human-design  — только если время известно
//    /bazi          — только если время известно И есть координаты
//
//  Если эндпоинт упал — пишет ошибку в result.error_*, не крашит пайп.
// ══════════════════════════════════════════════════════════════

const d = $input.first().json;
const BASE_URL = 'http://astrology:8000';

// ── Нормализация даты DD.MM.YYYY → YYYY-MM-DD ──
const [dd, mm, yyyy] = d.birthdate.split('.');
const birth_date = `${yyyy}-${mm}-${dd}`;

const hasTime = Boolean(d.birthtime) && d.birthtime.toUpperCase() !== 'UNKNOWN';
const hasCoords = d.lat != null && d.lon != null;

// Нормализация пола: принимаем русский и английский варианты
function normalizeGender(raw) {
  if (!raw) return 'male';
  const s = raw.toLowerCase();
  if (s === 'female' || s === 'женский' || s === 'женщина' || s === 'ж') return 'female';
  return 'male'; // дефолт
}
const gender = normalizeGender(d.gender);

// ── Базовый payload (общий для всех эндпоинтов) ──
const basePayload = {
  birth_date,
  birth_time: d.birthtime || null,
  timezone:   Number(d.timezone ?? 0),
  latitude:   hasCoords ? d.lat  : null,
  longitude:  hasCoords ? d.lon  : null,
  gender,
};

// ── Вызов сервиса ──
async function callService(path, extraPayload = {}) {
  const body = { ...basePayload, ...extraPayload };
  const res = await fetch(`${BASE_URL}${path}`, {
    method:  'POST',
    headers: { 'Content-Type': 'application/json' },
    body:    JSON.stringify(body),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`${path} → HTTP ${res.status}: ${text}`);
  }
  return res.json();
}

// ── Параллельные вызовы ──
const result = { ...d, birth_date };

// Jyotish — всегда (без времени вернёт time_sensitive: true)
try {
  result.jyotish = await callService('/jyotish');
} catch (e) {
  result.jyotish = null;
  result.error_jyotish = e.message;
}

// Western — всегда
try {
  result.western = await callService('/western');
} catch (e) {
  result.western = null;
  result.error_western = e.message;
}

// Human Design — только если время известно
if (hasTime) {
  try {
    result.human_design = await callService('/human-design');
  } catch (e) {
    result.human_design = null;
    result.error_human_design = e.message;
  }
} else {
  result.human_design = null;
  result.hd_skipped = 'birth_time unknown — HD требует точного времени рождения';
}

// Bazi — только если время известно (для час-столпа и true solar time)
// Без времени сервис вернёт столпы без часового, что корректно,
// но lon нужен в любом случае для true solar time.
if (hasCoords) {
  try {
    result.bazi = await callService('/bazi');
  } catch (e) {
    result.bazi = null;
    result.error_bazi = e.message;
  }
} else {
  result.bazi = null;
  result.bazi_skipped = 'координаты не определены — /bazi требует longitude для true solar time';
}

// ── Сводка по TIME-SENSITIVE флагам ──
result.time_sensitive_summary = {
  has_birth_time: hasTime,
  has_coordinates: hasCoords,
  affected: [
    ...(!hasTime ? ['HD (пропущен)', 'Лагна/ASC', 'Час-столп Бацзы', 'Дома'] : []),
    ...(!hasCoords ? ['Bazi (пропущен)', 'Лагна/ASC', 'Дома'] : []),
  ],
};

return [{ json: result }];

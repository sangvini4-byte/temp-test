// =============================================================
//  Лунные сутки по дате рождения — n8n Code Node
//  Входные поля (json):
//    birthDate  — строка "YYYY-MM-DD" (обязательно)
//    birthTime  — строка "HH:MM"      (по умолчанию "12:00")
//    timezone   — число, UTC-смещение (по умолчанию 0)
//  Точность: Солнце < 0.01°, Луна ~0.3° — достаточно для
//  определения лунных суток и накшатры вне граничных значений
// =============================================================


// ─── Юлианская дата ──────────────────────────────────────────

function toJD(year, month, day, hour, min) {
  if (month <= 2) { year--; month += 12; }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) +
         Math.floor(30.6001 * (month + 1)) +
         day + B - 1524.5 +
         (hour + min / 60) / 24;
}


// ─── Утилиты ─────────────────────────────────────────────────

const rad     = deg => deg * Math.PI / 180;
const norm360 = x   => ((x % 360) + 360) % 360;


// ─── Истинная долгота Солнца (Meeus гл. 25, погрешность < 0.01°) ─

function trueSolarLongitude(jd) {
  const T  = (jd - 2451545.0) / 36525;
  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M  = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  // Уравнение центра
  const C  = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(rad(M))
           + (0.019993 - 0.000101 * T) * Math.sin(rad(2 * M))
           +  0.000289 * Math.sin(rad(3 * M));
  return norm360(L0 + C);
}


// ─── Истинная долгота Луны (Meeus гл. 47, погрешность ~0.3°) ─
//  Включены все члены возмущений > 0.01°

function trueMoonLongitude(jd) {
  const T  = (jd - 2451545.0) / 36525;

  // Фундаментальные аргументы
  const L  = 218.3164477 + 481267.88123421 * T; // средняя долгота Луны
  const M  = 357.5291092 +  35999.0502909  * T; // средняя аномалия Солнца
  const Mp = 134.9633964 + 477198.8675055  * T; // средняя аномалия Луны
  const D  = 297.8501921 + 445267.1114034  * T; // средняя элонгация Луны
  const F  =  93.2720950 + 483202.0175233  * T; // аргумент широты Луны

  // Члены возмущений в долготе, градусы
  const dL = 6.289  * Math.sin(rad(Mp))          // главная аномалия
           + 1.274  * Math.sin(rad(2*D - Mp))     // эвекция
           + 0.658  * Math.sin(rad(2*D))          // вариация
           + 0.214  * Math.sin(rad(2*Mp))
           - 0.186  * Math.sin(rad(M))            // годовое уравнение
           - 0.114  * Math.sin(rad(2*F))          // редукция к эклиптике
           + 0.059  * Math.sin(rad(2*D - 2*Mp))
           + 0.057  * Math.sin(rad(2*D - M - Mp))
           + 0.053  * Math.sin(rad(2*D + Mp))
           + 0.046  * Math.sin(rad(2*D - M))
           - 0.041  * Math.sin(rad(M - Mp))
           - 0.035  * Math.sin(rad(D))
           - 0.030  * Math.sin(rad(M + Mp));

  return norm360(L + dL);
}


// ─── Айянамша Лахири (приближённая) ──────────────────────────

function lahiriAyanamsha(jd) {
  const yearsSinceJ2000 = (jd - 2451545.0) / 365.25;
  // Значение на J2000.0: 23°51'11.4" = 23.85317°
  // Прецессия: 50.29" / год = 0.013969° / год
  return norm360(23.85317 + yearsSinceJ2000 * (50.29 / 3600));
}


// ─── Справочник накшатр ───────────────────────────────────────

const NAKSHATRAS = [
  "Ashwini",         "Bharani",           "Krittika",
  "Rohini",          "Mrigashirsha",      "Ardra",
  "Punarvasu",       "Pushya",            "Ashlesha",
  "Magha",           "Purva Phalguni",    "Uttara Phalguni",
  "Hasta",           "Chitra",            "Swati",
  "Vishakha",        "Anuradha",          "Jyeshtha",
  "Mula",            "Purva Ashadha",     "Uttara Ashadha",
  "Shravana",        "Dhanishtha",        "Shatabhisha",
  "Purva Bhadrapada","Uttara Bhadrapada", "Revati"
];


// ─── Валидация ────────────────────────────────────────────────

function validateDate(str) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(str)) return false;
  const [y, m, d] = str.split('-').map(Number);
  const dt = new Date(Date.UTC(y, m - 1, d));
  return dt.getUTCFullYear() === y &&
         dt.getUTCMonth() + 1 === m &&
         dt.getUTCDate()  === d;
}

function validateTime(str) {
  return /^\d{1,2}:\d{2}$/.test(str);
}


// ─── Основной расчёт ─────────────────────────────────────────

try {
  const input     = $input.first().json;           // для нескольких айтемов замени на $input.all() с циклом
  const birthDate = input.birthDate;
  const birthTime = input.birthTime || "12:00";
  const timezone  = Number(input.timezone ?? 0);   // ?? вместо || — чтобы явный 0 не игнорировался

  // Валидация
  if (!birthDate)
    throw new Error("birthDate is required");
  if (!validateDate(birthDate))
    throw new Error("Invalid birthDate. Use YYYY-MM-DD");
  if (!validateTime(birthTime))
    throw new Error("Invalid birthTime. Use HH:MM");
  if (isNaN(timezone) || timezone < -14 || timezone > 14)
    throw new Error("timezone must be a number between -14 and 14 (e.g. 3 or -5.5)");

  const [year, month, day] = birthDate.split('-').map(Number);
  const [hour, minute]     = birthTime.split(':').map(Number);

  // Перевод в JD UTC
  const jd = toJD(year, month, day, hour, minute) - timezone / 24;

  // Долготы светил
  const sunLon  = trueSolarLongitude(jd);
  const moonLon = trueMoonLongitude(jd);

  // Лунные сутки (титхи): каждые 12° элонгации = 1 сутки, всего 30
  const diff          = norm360(moonLon - sunLon);
  const tithi         = Math.floor(diff / 12) + 1; // 1..30
  const paksha        = tithi <= 15 ? "Shukla" : "Krishna";
  const tithiInPaksha = tithi <= 15 ? tithi : tithi - 15;

  // Западная фаза
  let phase;
  if      (diff < 22.5 || diff >= 337.5) phase = "New Moon";
  else if (diff < 67.5)                  phase = "Waxing Crescent";
  else if (diff < 112.5)                 phase = "First Quarter";
  else if (diff < 157.5)                 phase = "Waxing Gibbous";
  else if (diff < 202.5)                 phase = "Full Moon";
  else if (diff < 247.5)                 phase = "Waning Gibbous";
  else if (diff < 292.5)                 phase = "Last Quarter";
  else                                   phase = "Waning Crescent";

  // Освещённость диска Луны
  const illumination = Math.round((1 - Math.cos(rad(diff))) / 2 * 100);

  // Накшатра и пада (сидерические координаты по Лахири)
  const NAKSHATRA_SIZE = 360 / 27;      // 13°20' = 13.3333...°
  const PADA_SIZE      = NAKSHATRA_SIZE / 4; // 3°20'
  const ayanamsha      = lahiriAyanamsha(jd);
  const moonSidereal   = norm360(moonLon - ayanamsha);
  const nakshatraIndex = Math.floor(moonSidereal / NAKSHATRA_SIZE);
  const pada           = Math.floor((moonSidereal % NAKSHATRA_SIZE) / PADA_SIZE) + 1;
  const nakshatra      = NAKSHATRAS[nakshatraIndex] ?? "Unknown";

  return [{
    json: {
      lunar_day:               tithi,
      paksha:                  paksha,
      tithi_in_paksha:         tithiInPaksha,
      phase:                   phase,
      illumination_percent:    illumination,
      nakshatra:               nakshatra,
      pada:                    pada,
      moon_longitude_tropical: +moonLon.toFixed(3),
      sun_longitude_tropical:  +sunLon.toFixed(3),
      ayanamsha_used:          +ayanamsha.toFixed(3),
    }
  }];

} catch (e) {
  return [{ json: { error: e.message } }];
}

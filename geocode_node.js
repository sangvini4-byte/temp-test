// ══════════════════════════════════════════════════════════════
//  n8n Code Node — "Parse Geocode Result"
//  Ставится ПОСЛЕ HTTP Request ноды "Geocode — Lookup Coordinates"
//  (Nominatim/OpenStreetMap, бесплатно, без API-ключа).
//
//  Nominatim возвращает JSON-массив объектов вида:
//    [{ "lat": "55.7558", "lon": "37.6173", "display_name": "...", ... }]
//
//  n8n иногда раскладывает такой массив на отдельные item'ы (тогда
//  $input.first().json уже сам объект), а иногда отдаёт как один item
//  с массивом внутри (зависит от версии/настроек ноды) — обрабатываем
//  оба случая, чтобы не сломаться на конкретной версии n8n.
// ══════════════════════════════════════════════════════════════

const raw = $input.first().json;

// Если предыдущая нода была переименована — поменяй имя в кавычках ниже.
const prev = $('Validate Input').item.json;

let lat = null;
let lon = null;
let geocode_error = null;

// Вариант А: объект уже сам результат геокодирования ({lat, lon, ...})
// Вариант Б: объект-обёртка с массивом результатов (например {data: [...]})
let candidate = raw;
if (!candidate?.lat && Array.isArray(raw)) {
  candidate = raw[0];
} else if (!candidate?.lat && Array.isArray(raw?.data)) {
  candidate = raw.data[0];
}

if (candidate && candidate.lat !== undefined && candidate.lon !== undefined) {
  lat = parseFloat(candidate.lat);
  lon = parseFloat(candidate.lon);
  if (Number.isNaN(lat) || Number.isNaN(lon)) {
    lat = null;
    lon = null;
    geocode_error = `Geocode вернул нечисловые координаты для "${prev.birthplace}"`;
  }
} else {
  geocode_error = `Не удалось геокодировать "${prev.birthplace}" — продолжаем без координат`;
}

// ВАЖНО: без lat/lon сервис /human-design откажет (400, время без координат
// бессмысленно для асцендента), а /jyotish и /western отработают нормально,
// но без асцендента/домов (time_sensitive-логика на стороне сервиса).
return [{ json: { ...prev, lat, lon, geocode_error } }];

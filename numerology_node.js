// ========== ТАБЛИЦЫ ЗНАЧЕНИЙ БУКВ ==========

const latinTable = {
  a:1, b:2, c:3, d:4, e:5, f:6, g:7, h:8, i:9,
  j:1, k:2, l:3, m:4, n:5, o:6, p:7, q:8, r:9,
  s:1, t:2, u:3, v:4, w:5, x:6, y:7, z:8
};

// Классическая русская нумерология (школа Ладини)
const cyrillicTable = {
  'а':1, 'б':2, 'в':3, 'г':4, 'д':5, 'е':6, 'ё':7, 'ж':8, 'з':9,
  'и':1, 'й':1, 'к':2, 'л':3, 'м':4, 'н':5, 'о':6, 'п':7, 'р':8,
  'с':9, 'т':1, 'у':2, 'ф':3, 'х':4, 'ц':5, 'ч':6, 'ш':7, 'щ':8,
  'ъ':0, 'ы':1, 'ь':0, 'э':4, 'ю':5, 'я':6
};

// ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ==========

function sumDigits(num) {
  let sum = 0;
  while (num > 0) {
    sum += num % 10;
    num = Math.floor(num / 10);
  }
  return sum;
}

// ✅ ИСПРАВЛЕНО: проверка мастер-числа после каждой итерации
function reduceToMaster(num) {
  if (num === 11 || num === 22 || num === 33) return num;
  while (num > 9) {
    num = sumDigits(num);
    if (num === 11 || num === 22 || num === 33) return num;
  }
  return num;
}

// Свёртка до 1–22 с сохранением 11 и 22
function reduceTo22(num) {
  while (num > 22) {
    num = sumDigits(num);
    if (num === 11 || num === 22) return num;
  }
  return num;
}

// Приведение к аркану 1–22 (0 → 22)
function mod22(num) {
  const res = num % 22;
  return res === 0 ? 22 : res;
}

// Числовое значение буквы
function getCharValue(ch) {
  if (ch in latinTable) return latinTable[ch];
  if (ch in cyrillicTable) return cyrillicTable[ch];
  return 0;
}

// Число имени (все буквы)
function nameNumber(name) {
  const clean = name.toLowerCase().replace(/[^a-zа-яё]/g, '');
  let sum = 0;
  for (const ch of clean) sum += getCharValue(ch);
  return reduceToMaster(sum);
}

// Число души (только гласные)
function soulUrgeNumber(name) {
  const vowelsLatin   = new Set(['a','e','i','o','u','y']);
  const vowelsCyrillic = new Set(['а','е','ё','и','о','у','ы','э','ю','я']);
  const clean = name.toLowerCase().replace(/[^a-zа-яё]/g, '');
  let sum = 0;
  for (const ch of clean) {
    if (vowelsLatin.has(ch) || vowelsCyrillic.has(ch)) sum += getCharValue(ch);
  }
  return reduceToMaster(sum);
}

// Число личности (только согласные)
function personalityNumber(name) {
  const vowelsLatin    = new Set(['a','e','i','o','u','y']);
  const vowelsCyrillic = new Set(['а','е','ё','и','о','у','ы','э','ю','я']);
  const silentCyrillic = new Set(['ъ','ь']);
  const clean = name.toLowerCase().replace(/[^a-zа-яё]/g, '');
  let sum = 0;
  for (const ch of clean) {
    if (!vowelsLatin.has(ch) && !vowelsCyrillic.has(ch) && !silentCyrillic.has(ch)) {
      sum += getCharValue(ch);
    }
  }
  return reduceToMaster(sum);
}

// ========== ОСНОВНОЙ РАСЧЁТ ==========

try {
  const input = $input.item.json;
  const { birthDate, fullName } = input;
  const currentYear = input.currentYear ?? new Date().getFullYear();

  if (!birthDate || !fullName) {
    throw new Error("Missing required fields: birthDate, fullName");
  }

  const [year, month, day] = birthDate.split('-').map(Number);
  if (!year || !month || !day) throw new Error("Invalid birthDate format, expected YYYY-MM-DD");

  // ── Классическая нумерология ──────────────────────────────

  // Компоненты сворачиваем отдельно, сохраняя мастер-числа
  const dayReduced   = reduceToMaster(day);
  const monthReduced = reduceToMaster(month);
  const yearReduced  = reduceToMaster(year);       // год целиком

  const lifePath   = reduceToMaster(dayReduced + monthReduced + yearReduced);
  const destiny    = nameNumber(fullName);
  const soulUrge   = soulUrgeNumber(fullName);
  const personality = personalityNumber(fullName);
  const birthday   = reduceToMaster(day);

  const personalYear = reduceToMaster(
    dayReduced + monthReduced + reduceToMaster(currentYear)
  );
  const personalMonth = reduceToMaster(personalYear + month);

  // Кармические числа (карма присутствует если в числе имени есть 13,14,16,19)
  const nameRaw = (() => {
    const clean = fullName.toLowerCase().replace(/[^a-zа-яё]/g, '');
    let s = 0;
    for (const ch of clean) s += getCharValue(ch);
    return s;
  })();
  const karmicDebts = [13, 14, 16, 19].filter(k => {
    // Кармический долг присутствует, если при последовательной свёртке имени
    // одним из промежуточных значений является одно из этих чисел
    let n = nameRaw;
    while (n > 22) { if (n === k) return true; n = sumDigits(n); }
    return n === k;
  });

  // ── Матрица Судьбы (Ладини) ───────────────────────────────

  const A = mod22(day);
  const B = mod22(month);

  // Год: сначала складываем цифры, затем свёртка до 1–22 с сохранением 11 и 22
  const yearDigitSum = sumDigits(year);
  const C = mod22(reduceTo22(yearDigitSum));

  const D      = mod22(A + B + C);
  const center = mod22(A + B + C + D);

  // 3×3 сетка (стандартная раскладка Ладини)
  const grid = [
    [ A,              mod22(A + B), B              ],
    [ mod22(A + C),   center,       mod22(B + C)   ],
    [ C,              D,            mod22(B + D)   ]
  ];

  // Ключевые точки матрицы
  const comfortZone  = grid[0][1];          // центр верхней стороны
  const mainTask     = mod22(A + B + C + D); // = center (общая задача)
  const higherPurpose = grid[1][2];          // mod22(B + C)
  const karmicTail   = [grid[2][0], grid[2][1], grid[2][2]]; // нижняя строка

  // Повторяющиеся арканы (встречаются 2+ раз в сетке)
  const allValues = grid.flat();
  const freq = {};
  for (const v of allValues) freq[v] = (freq[v] || 0) + 1;
  const repeatingArcana = Object.entries(freq)
    .filter(([, count]) => count > 1)
    .map(([k]) => Number(k))
    .sort((a, b) => a - b);

  // ── Возврат ───────────────────────────────────────────────

  return {
    classical: {
      life_path:      lifePath,
      destiny:        destiny,
      soul_urge:      soulUrge,
      personality:    personality,
      birthday:       birthday,
      personal_year:  personalYear,
      personal_month: personalMonth,
      karmic_debts:   karmicDebts       // [] если нет
    },
    matrix: {
      core:             center,
      comfort_zone:     comfortZone,
      main_task:        mainTask,
      higher_purpose:   higherPurpose,
      karmic_tail:      karmicTail,
      grid:             grid,
      repeating_arcana: repeatingArcana
    },
    debug: {
      day_reduced:  dayReduced,
      month_reduced: monthReduced,
      year_reduced:  yearReduced,
      A, B, C, D
    }
  };

} catch (e) {
  return { error: e.message };
}

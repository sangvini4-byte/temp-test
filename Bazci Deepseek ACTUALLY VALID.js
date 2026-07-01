// ========== АСТРОНОМИЧЕСКИЕ ФУНКЦИИ ==========

function toJD(year, month, day, hour, min, sec) {
  if (month <= 2) { year--; month += 12; }
  const A = Math.floor(year / 100);
  const B = 2 - A + Math.floor(A / 4);
  return Math.floor(365.25 * (year + 4716)) +
         Math.floor(30.6001 * (month + 1)) +
         day + B - 1524.5 +
         (hour + min / 60 + sec / 3600) / 24;
}

function solarLongitude(jd) {
  const T = (jd - 2451545.0) / 36525;
  let L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const C = (1.914602 - 0.004817 * T - 0.000014 * T * T) * Math.sin(M * Math.PI / 180) +
            (0.019993 - 0.000101 * T) * Math.sin(2 * M * Math.PI / 180) +
            0.000289 * Math.sin(3 * M * Math.PI / 180);
  let L = L0 + C;
  const omega = 125.04 - 1934.136 * T;
  L += 0.00569 - 0.00478 * Math.sin(omega * Math.PI / 180);
  return L % 360;
}

function findSolarTerm(year, longitude) {
  let jd = toJD(year, 1, 1, 0, 0, 0);
  let L = solarLongitude(jd) % 360;
  let days = ((longitude - L + 360) % 360) / 0.9856;
  jd += days;
  for (let i = 0; i < 5; i++) {
    L = solarLongitude(jd) % 360;
    const delta = ((longitude - L + 180) % 360) - 180;
    if (Math.abs(delta) < 0.0001) break;
    jd += delta / 0.9856;
  }
  return jd;
}

function getAllSolarTerms(year) {
  const terms = [];
  const names = [
    "Li Chun", "Yu Shui", "Jing Zhe", "Chun Fen", "Qing Ming", "Gu Yu",
    "Li Xia", "Xiao Man", "Mang Zhong", "Xia Zhi", "Xiao Shu", "Da Shu",
    "Li Qiu", "Chu Shu", "Bai Lu", "Qiu Fen", "Han Lu", "Shuang Jiang",
    "Li Dong", "Xiao Xue", "Da Xue", "Dong Zhi", "Xiao Han", "Da Han"
  ];
  const startAngle = 315; // Li Chun
  for (let i = 0; i < 24; i++) {
    const angle = (startAngle + i * 15) % 360;
    const jd = findSolarTerm(year, angle);
    terms.push({ name: names[i], angle, jd, solarMonth: Math.floor(i / 2) % 12 });
  }
  return terms;
}

function equationOfTime(jd) {
  const T = (jd - 2451545.0) / 36525;
  const L0 = 280.46646 + 36000.76983 * T + 0.0003032 * T * T;
  const M = 357.52911 + 35999.05029 * T - 0.0001537 * T * T;
  const eps = (23.439 - 0.013 * T) * Math.PI / 180;
  const y = Math.tan(eps / 2) ** 2;
  const e = 0.016708634 - 0.000042037 * T - 0.0000001267 * T * T;
  const EoT = (y * Math.sin(2 * L0 * Math.PI / 180) 
             - 2 * e * Math.sin(M * Math.PI / 180)
             + 4 * e * y * Math.sin(M * Math.PI / 180) * Math.cos(2 * L0 * Math.PI / 180)
             - 0.5 * y * y * Math.sin(4 * L0 * Math.PI / 180)
             - 1.25 * e * e * Math.sin(2 * M * Math.PI / 180)) * 4;
  return EoT; // минуты
}

function trueSolarTime(utcHour, utcMin, longitude, year, month, day) {
  const jd = toJD(year, month, day, 0, 0, 0);
  const eot = equationOfTime(jd);
  const meanSolar = utcHour + utcMin / 60 + longitude / 15;
  return (meanSolar + eot / 60 + 24) % 24;
}

// ========== КИТАЙСКИЙ КАЛЕНДАРЬ ==========

const STEMS = ["Jia", "Yi", "Bing", "Ding", "Wu", "Ji", "Geng", "Xin", "Ren", "Gui"];
const BRANCHES = ["Zi", "Chou", "Yin", "Mao", "Chen", "Si", "Wu", "Wei", "Shen", "You", "Xu", "Hai"];
const ELEMENTS = ["Wood", "Wood", "Fire", "Fire", "Earth", "Earth", "Metal", "Metal", "Water", "Water"];
const YIN_YANG = ["Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin", "Yang", "Yin"];

const HOUR_STEM_TABLE = [
  [0,0,1,1,2,2,3,3,4,4], // Jia/Ji
  [2,2,3,3,4,4,5,5,6,6], // Yi/Geng
  [4,4,5,5,6,6,7,7,8,8], // Bing/Xin
  [6,6,7,7,8,8,9,9,0,0], // Ding/Ren
  [8,8,9,9,0,0,1,1,2,2]  // Wu/Gui
];

// Исправленная таблица Десяти Богов
const GODS = [
  // Jia (Yang Wood)
  ["DM","JC","EG","HO","IW","DW","7K","DO","IR","DR"],
  // Yi (Yin Wood)
  ["JC","DM","HO","EG","DW","IW","DO","7K","DR","IR"],
  // Bing (Yang Fire)
  ["IR","DR","DM","JC","EG","HO","IW","DW","7K","DO"],
  // Ding (Yin Fire)
  ["DR","IR","JC","DM","HO","EG","DW","IW","DO","7K"],
  // Wu (Yang Earth)
  ["7K","DO","IR","DR","DM","JC","EG","HO","IW","DW"],
  // Ji (Yin Earth)
  ["DO","7K","DR","IR","JC","DM","HO","EG","DW","IW"],
  // Geng (Yang Metal)
  ["IW","DW","7K","DO","IR","DR","DM","JC","EG","HO"],
  // Xin (Yin Metal)
  ["DW","IW","DO","7K","DR","IR","JC","DM","HO","EG"],
  // Ren (Yang Water)
  ["EG","HO","IW","DW","7K","DO","IR","DR","DM","JC"],
  // Gui (Yin Water)
  ["HO","EG","DW","IW","DO","7K","DR","IR","JC","DM"]
];

const GOD_NAMES = {
  DM: "Day Master", JC: "Jie Cai", EG: "Eating God", HO: "Hurting Officer",
  IW: "Indirect Wealth", DW: "Direct Wealth", "7K": "Seven Killings",
  DO: "Direct Officer", IR: "Indirect Resource", DR: "Direct Resource"
};

// ========== ОСНОВНОЙ РАСЧЁТ ==========

try {
  const input = $input.item.json;
  const birthDate = input.birthDate;   // "YYYY-MM-DD"
  const birthTime = input.birthTime;   // "HH:MM" локальное
  const tzOffset = input.timezone;     // UTC offset in hours
  const longitude = input.longitude;   // decimal degrees (east positive)
  const gender = input.gender;         // "male" / "female"

  if (!birthDate || !birthTime || tzOffset === undefined || longitude === undefined || !gender) {
    throw new Error("Missing required input fields: birthDate, birthTime, timezone, longitude, gender");
  }

  const [year, month, day] = birthDate.split('-').map(Number);
  const [hour, minute] = birthTime.split(':').map(Number);

  // UTC time
  const utcHour = hour - tzOffset;
  const utcMin = minute;

  // True solar time for hour pillar
  const trueSolar = trueSolarTime(utcHour, utcMin, longitude, year, month, day);

  // Hour branch (double-hour period)
  // Note: Zi hour (23:00-00:59) is assigned to the next day by convention here.
  let hourBranchIndex;
  if (trueSolar >= 23 || trueSolar < 1) hourBranchIndex = 0;
  else hourBranchIndex = Math.floor((trueSolar + 1) / 2) % 12;

  // Solar year and terms
  let termsCurrent = getAllSolarTerms(year);
  let termsPrev = getAllSolarTerms(year - 1);

  const birthJD = toJD(year, month, day, utcHour, utcMin, 0);

  // Li Chun JD
  const liChunJD = termsCurrent.find(t => t.angle === 315)?.jd;
  if (liChunJD === undefined) throw new Error("Cannot find Li Chun for year");

  let solarYear, termsAll;
  if (birthJD < liChunJD) {
    solarYear = year - 1;
    termsAll = termsPrev;
  } else {
    solarYear = year;
    termsAll = termsCurrent;
  }

  // Filter only jié terms (even indices: 0,2,4,...,22) and sort by JD
  const jieTerms = termsAll
    .filter((_, i) => i % 2 === 0)   // только jié
    .sort((a, b) => a.jd - b.jd);

  // Month index: which jie term is before birth?
  let solarMonthIndex = -1;
  for (let i = 0; i < jieTerms.length; i++) {
    if (birthJD >= jieTerms[i].jd) {
      solarMonthIndex = i;
    } else {
      break;
    }
  }
  // If before Li Chun (first jie), adjust to previous year's last month
  if (solarMonthIndex === -1) {
    // Use previous year's last jie (which is in termsPrev)
    const prevJie = termsPrev
      .filter((_, i) => i % 2 === 0)
      .sort((a, b) => a.jd - b.jd);
    solarMonthIndex = 11; // last month of previous solar year
    solarYear = year - 1;
    // We'll need the correct year stem/branch for previous year
  }

  // Year pillar
  const yearStemIndex = (solarYear - 4) % 10;
  const yearBranchIndex = (solarYear - 4) % 12;

  // Month pillar
  const monthStemIndex = (yearStemIndex * 2 + solarMonthIndex) % 10;
  const monthBranchIndex = (solarMonthIndex + 2) % 12;

  // Day pillar (counting from 1 Jan 1900, Jia Xu = index 10 in 60-cycle)
  const refDate = new Date(Date.UTC(1900, 0, 1));
  const birthDateOnly = new Date(Date.UTC(year, month - 1, day));
  const diffDays = Math.floor((birthDateOnly.getTime() - refDate.getTime()) / 86400000);
  const dayCycleIndex = (diffDays + 10) % 60;
  const dayStemIndex = dayCycleIndex % 10;
  const dayBranchIndex = dayCycleIndex % 12;

  // Hour pillar
  const hourStemIndex = HOUR_STEM_TABLE[dayStemIndex % 5][hourBranchIndex];

  // Ten Gods
  const tenGods = {
    year: GOD_NAMES[ GODS[dayStemIndex][yearStemIndex] ],
    month: GOD_NAMES[ GODS[dayStemIndex][monthStemIndex] ],
    day: "Day Master",
    hour: GOD_NAMES[ GODS[dayStemIndex][hourStemIndex] ]
  };

  // Clashes
  const branchClash = {
    Zi:"Wu",Chou:"Wei",Yin:"Shen",Mao:"You",Chen:"Xu",Si:"Hai",
    Wu:"Zi",Wei:"Chou",Shen:"Yin",You:"Mao",Xu:"Chen",Hai:"Si"
  };
  const stemClash = {
    Jia:"Geng",Yi:"Xin",Bing:"Ren",Ding:"Gui",
    Geng:"Jia",Xin:"Yi",Ren:"Bing",Gui:"Ding"
  };
  const clashes = [];
  function addClash(type, a, b, labelA, labelB) {
    if (a === b) return;
    if ((type === 'branch' && branchClash[a] === b) || (type === 'stem' && stemClash[a] === b)) {
      clashes.push(`${labelA} ${a} clashes ${labelB} ${b}`);
    }
  }
  const pillars = [
    { stem: yearStemIndex, branch: yearBranchIndex, label: "Year" },
    { stem: monthStemIndex, branch: monthBranchIndex, label: "Month" },
    { stem: dayStemIndex, branch: dayBranchIndex, label: "Day" },
    { stem: hourStemIndex, branch: hourBranchIndex, label: "Hour" }
  ];
  for (let i = 0; i < pillars.length; i++) {
    for (let j = i + 1; j < pillars.length; j++) {
      addClash('branch', BRANCHES[pillars[i].branch], BRANCHES[pillars[j].branch], pillars[i].label, pillars[j].label);
      addClash('stem', STEMS[pillars[i].stem], STEMS[pillars[j].stem], pillars[i].label, pillars[j].label);
    }
  }

  // Luck Pillar calculation
  const isYangYear = yearStemIndex % 2 === 0;
  const forward = (gender === "male" && isYangYear) || (gender === "female" && !isYangYear);

  // Find the next (or previous) jie term relative to birth for luck start age
  let anchorJD;
  if (forward) {
    // next jie after birth
    const nextJie = jieTerms.find(t => t.jd > birthJD);
    if (nextJie) anchorJD = nextJie.jd;
    else {
      // take first jie of next year
      const nextYearTerms = getAllSolarTerms(solarYear + 1);
      const firstJieNext = nextYearTerms.filter((_, i) => i % 2 === 0).sort((a, b) => a.jd - b.jd);
      anchorJD = firstJieNext[0]?.jd;
      if (!anchorJD) throw new Error("Cannot find anchor for luck start");
    }
  } else {
    // previous jie before birth
    const prevJie = [...jieTerms].reverse().find(t => t.jd < birthJD);
    if (prevJie) anchorJD = prevJie.jd;
    else {
      // last jie of previous year
      const prevYearTerms = getAllSolarTerms(solarYear - 1);
      const lastJiePrev = prevYearTerms.filter((_, i) => i % 2 === 0).sort((a, b) => a.jd - b.jd).pop();
      anchorJD = lastJiePrev?.jd;
      if (!anchorJD) throw new Error("Cannot find anchor for luck start");
    }
  }

  const diffInDays = Math.abs(anchorJD - birthJD);
  const luckStartAge = Math.round(diffInDays / 3 * 10) / 10;

  // Current luck pillar: start with the pillar next to month pillar
  const step = forward ? 1 : -1;
  let luckStem = (monthStemIndex + step + 10) % 10;
  let luckBranch = (monthBranchIndex + step + 12) % 12;
  let age = luckStartAge;
  const now = new Date();
  const currentAge = now.getFullYear() - year + 
    (now.getMonth() >= month - 1 && now.getDate() >= day ? 0 : -1);

  while (age + 10 <= currentAge) {
    age += 10;
    luckStem = (luckStem + step + 10) % 10;
    luckBranch = (luckBranch + step + 12) % 12;
  }

  const currentLuckPillar = `${STEMS[luckStem]} ${BRANCHES[luckBranch]}`;
  const nextLuckStem = (luckStem + step + 10) % 10;
  const nextLuckBranch = (luckBranch + step + 12) % 12;
  const upcomingLuckPillar = `${STEMS[nextLuckStem]} ${BRANCHES[nextLuckBranch]}`;

  // Output
  const result = {
    year_pillar_stem: STEMS[yearStemIndex],
    year_pillar_branch: BRANCHES[yearBranchIndex],
    month_pillar_stem: STEMS[monthStemIndex],
    month_pillar_branch: BRANCHES[monthBranchIndex],
    day_pillar_stem: STEMS[dayStemIndex],
    day_pillar_branch: BRANCHES[dayBranchIndex],
    hour_pillar_stem: STEMS[hourStemIndex],
    hour_pillar_branch: BRANCHES[hourBranchIndex],
    day_master_element: ELEMENTS[dayStemIndex],
    day_master_yin_yang: YIN_YANG[dayStemIndex],
    ten_gods: tenGods,
    luck_pillar_current: currentLuckPillar,
    luck_pillar_upcoming: upcomingLuckPillar,
    luck_start_age: luckStartAge,
    clash_patterns: clashes,
    true_solar_time: +trueSolar.toFixed(2),
    solar_year: solarYear,
    solar_month_index: solarMonthIndex
  };

  return result;

} catch (e) {
  return { error: e.message };
}
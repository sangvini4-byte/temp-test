// ========== FIXED CORE SECTION ==========
// Drop-in replacement for the main calculation block.
// Astronomical functions and lookup tables above this point are UNCHANGED.
// Fixes: negative modulo, day pillar anchor date, late-Zi hour, hidden stems.

const HIDDEN_STEMS = {
  Zi:["Gui"], Chou:["Ji","Gui","Xin"], Yin:["Jia","Bing","Wu"],
  Mao:["Yi"], Chen:["Wu","Yi","Gui"], Si:["Bing","Geng","Wu"],
  Wu:["Ding","Bing","Wu"], Wei:["Ji","Yi","Ding"], Shen:["Geng","Ren","Wu"],
  You:["Xin"], Xu:["Wu","Ding","Xin"], Hai:["Ren","Jia"]
};

function mod(n, m) { return ((n % m) + m) % m; }

try {
  const input = $input.item.json;
  const birthDate = input.birthDate;
  const birthTime = input.birthTime;
  const tzOffset  = input.timezone;
  const longitude = input.longitude;
  const gender    = input.gender;

  if (!birthDate || !birthTime || tzOffset === undefined || longitude === undefined || !gender)
    throw new Error("Missing: birthDate, birthTime, timezone, longitude, gender");

  const [year, month, day] = birthDate.split('-').map(Number);
  const [hour, minute]     = birthTime.split(':').map(Number);
  const utcHour = hour - tzOffset;

  const trueSolar = trueSolarTime(utcHour, minute, longitude, year, month, day);

  // FIX: Late Zi hour belongs to next day for Day Pillar purposes
  const isLateZi = trueSolar >= 23;
  const pillarDate = isLateZi
    ? new Date(Date.UTC(year, month - 1, day + 1))
    : new Date(Date.UTC(year, month - 1, day));

  let hourBranchIndex = (trueSolar >= 23 || trueSolar < 1)
    ? 0
    : Math.floor((trueSolar + 1) / 2) % 12;

  const termsCurrent = getAllSolarTerms(year);
  const termsPrev    = getAllSolarTerms(year - 1);
  const birthJD      = toJD(year, month, day, utcHour, minute, 0);
  const liChunJD     = termsCurrent.find(t => t.angle === 315)?.jd;
  if (!liChunJD) throw new Error("Cannot find Li Chun");

  // FIX: Determine solarYear and termsAll BEFORE building jieTerms
  let solarYear, termsAll;
  if (birthJD < liChunJD) { solarYear = year - 1; termsAll = termsPrev; }
  else                     { solarYear = year;     termsAll = termsCurrent; }

  const jieTerms = termsAll.filter((_, i) => i % 2 === 0).sort((a, b) => a.jd - b.jd);

  let solarMonthIndex = 11;
  for (let i = 0; i < jieTerms.length; i++) {
    if (birthJD >= jieTerms[i].jd) solarMonthIndex = i; else break;
  }

  // FIX: Safe modulo everywhere
  const yearStemIndex    = mod(solarYear - 4, 10);
  const yearBranchIndex  = mod(solarYear - 4, 12);
  const monthStemIndex   = mod(yearStemIndex * 2 + solarMonthIndex, 10);
  const monthBranchIndex = mod(solarMonthIndex + 2, 12);

  // FIX: Anchor = Jan 1 2000 = Jia Chen = position 4 in 60-cycle
  const ref = new Date(Date.UTC(2000, 0, 1));
  const diffDays      = Math.floor((pillarDate - ref) / 86400000);
  const dayCycleIndex = mod(diffDays + 4, 60);
  const dayStemIndex   = dayCycleIndex % 10;
  const dayBranchIndex = dayCycleIndex % 12;

  const hourStemIndex = HOUR_STEM_TABLE[dayStemIndex % 5][hourBranchIndex];

  function getTenGod(dayStem, targetStem) {
    return GOD_NAMES[GODS[dayStem][targetStem]];
  }
  function getHiddenGods(dayStem, branchName) {
    return (HIDDEN_STEMS[branchName] || []).map(s => {
      const idx = STEMS.indexOf(s);
      return idx >= 0 ? { stem: s, god: getTenGod(dayStem, idx) } : null;
    }).filter(Boolean);
  }

  const tenGods = {
    year:  getTenGod(dayStemIndex, yearStemIndex),
    month: getTenGod(dayStemIndex, monthStemIndex),
    day:   "Day Master",
    hour:  getTenGod(dayStemIndex, hourStemIndex),
  };
  const hiddenGods = {
    year:  getHiddenGods(dayStemIndex, BRANCHES[yearBranchIndex]),
    month: getHiddenGods(dayStemIndex, BRANCHES[monthBranchIndex]),
    day:   getHiddenGods(dayStemIndex, BRANCHES[dayBranchIndex]),
    hour:  getHiddenGods(dayStemIndex, BRANCHES[hourBranchIndex]),
  };

  const branchClash = {
    Zi:"Wu",Chou:"Wei",Yin:"Shen",Mao:"You",Chen:"Xu",Si:"Hai",
    Wu:"Zi",Wei:"Chou",Shen:"Yin",You:"Mao",Xu:"Chen",Hai:"Si"
  };
  const stemClash = {
    Jia:"Geng",Yi:"Xin",Bing:"Ren",Ding:"Gui",
    Geng:"Jia",Xin:"Yi",Ren:"Bing",Gui:"Ding"
  };
  const clashes = [];
  const pils = [
    {stem:yearStemIndex,  branch:yearBranchIndex,  label:"Year"},
    {stem:monthStemIndex, branch:monthBranchIndex, label:"Month"},
    {stem:dayStemIndex,   branch:dayBranchIndex,   label:"Day"},
    {stem:hourStemIndex,  branch:hourBranchIndex,  label:"Hour"},
  ];
  for (let i = 0; i < pils.length; i++)
    for (let j = i+1; j < pils.length; j++) {
      const [a, b] = [pils[i], pils[j]];
      const [sb, tb] = [BRANCHES[a.branch], BRANCHES[b.branch]];
      const [ss, ts] = [STEMS[a.stem],      STEMS[b.stem]];
      if (branchClash[sb] === tb) clashes.push(`${a.label} ${sb} clashes ${b.label} ${tb}`);
      if (stemClash[ss]   === ts) clashes.push(`${a.label} ${ss} clashes ${b.label} ${ts}`);
    }

  const isYangYear = yearStemIndex % 2 === 0;
  const forward = (gender === "male" && isYangYear) || (gender === "female" && !isYangYear);
  const step = forward ? 1 : -1;

  let anchorJD;
  if (forward) {
    const nj = jieTerms.find(t => t.jd > birthJD);
    anchorJD = nj?.jd ?? getAllSolarTerms(solarYear+1).filter((_,i)=>i%2===0).sort((a,b)=>a.jd-b.jd)[0]?.jd;
  } else {
    const pj = [...jieTerms].reverse().find(t => t.jd < birthJD);
    anchorJD = pj?.jd ?? getAllSolarTerms(solarYear-1).filter((_,i)=>i%2===0).sort((a,b)=>a.jd-b.jd).pop()?.jd;
  }
  if (!anchorJD) throw new Error("Cannot find luck pillar anchor");

  const luckStartAge = Math.round(Math.abs(anchorJD - birthJD) / 3 * 10) / 10;

  let luckStem   = mod(monthStemIndex   + step, 10);
  let luckBranch = mod(monthBranchIndex + step, 12);
  let age = luckStartAge;

  const now = new Date();
  const currentAge = now.getUTCFullYear() - year
    + ((now.getUTCMonth()+1 > month
      || (now.getUTCMonth()+1 === month && now.getUTCDate() >= day)) ? 0 : -1);

  while (age + 10 <= currentAge) {
    age += 10;
    luckStem   = mod(luckStem   + step, 10);
    luckBranch = mod(luckBranch + step, 12);
  }

  return {
    year_pillar:   { stem: STEMS[yearStemIndex],  branch: BRANCHES[yearBranchIndex]  },
    month_pillar:  { stem: STEMS[monthStemIndex], branch: BRANCHES[monthBranchIndex] },
    day_pillar:    { stem: STEMS[dayStemIndex],   branch: BRANCHES[dayBranchIndex]   },
    hour_pillar:   { stem: STEMS[hourStemIndex],  branch: BRANCHES[hourBranchIndex]  },
    day_master:    { element: ELEMENTS[dayStemIndex], yin_yang: YIN_YANG[dayStemIndex] },
    ten_gods:      tenGods,
    hidden_gods:   hiddenGods,
    luck_pillar:   {
      current:   `${STEMS[luckStem]} ${BRANCHES[luckBranch]}`,
      upcoming:  `${STEMS[mod(luckStem+step,10)]} ${BRANCHES[mod(luckBranch+step,12)]}`,
      start_age: luckStartAge,
    },
    clash_patterns:    clashes,
    late_zi_adjusted:  isLateZi,
    true_solar_time:   +trueSolar.toFixed(2),
    solar_year:        solarYear,
    solar_month_index: solarMonthIndex,
  };

} catch(e) { return { error: e.message }; }

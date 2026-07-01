// ═══════════════════════════════════════════════════════════════
//  INTERPRETATION LAYER — 7 Build Payload nodes
//  Каждый читает готовые данные калькулятора и строит LLM-запрос.
//  Модель ИНТЕРПРЕТИРУЕТ, не считает.
//
//  Предполагаемая структура d после Calculation Layer:
//    d.bazi          — из JS BaZi Code node
//    d.numerology    — из JS Numerology Code node { classical, matrix }
//    d.lunar         — из JS Lunar Code node
//    d.jyotish       — из Python /jyotish
//    d.western       — из Python /western
//    d.human_design  — из Python /hd
//    d.name, d.gender, d.birthdate, d.birthtime, d.birthplace
// ═══════════════════════════════════════════════════════════════


// ───────────────────────────────────────────────────────────────
//  NODE 1 — Build BaZi Interpreter Payload
//  Paste into: n8n Code node "Build BaZi Interp Payload"
//  Next node:  HTTP Request → DeepSeek /v1/chat/completions
// ───────────────────────────────────────────────────────────────

const buildBaziPayload = () => {
  const d = $input.first().json;
  const bazi = d.bazi;

  if (!bazi || bazi.error) {
    return [{ json: { ...d, output_bazi: `BaZi data unavailable: ${bazi?.error || 'no data'}` } }];
  }

  const prompt = `You are an expert in BaZi (Four Pillars of Destiny). 
The chart has already been calculated. DO NOT recalculate anything.
Your task is INTERPRETATION ONLY — every insight must reference specific values from the data below.

BIRTH DATA: ${d.name || 'Client'}, ${d.gender}, born ${d.birthdate} ${d.birthtime || 'time unknown'}, ${d.birthplace}

PRE-CALCULATED BAZI DATA:
${JSON.stringify(bazi, null, 2)}

INTERPRETATION INSTRUCTIONS:

## DAY MASTER ANALYSIS
State the Day Master element and polarity. Assess strength (strong/weak/neutral) based on which elements appear in the chart. Explain what this element in this polarity means as a core personality pattern — not generically, but using the specific stem name. 2–3 sentences.

## ELEMENTAL PROFILE
List all elements present across the four pillars (stems + branch hidden stems). Identify missing elements and what their absence typically creates. Name the dominant element and its practical expression. Use exact pillar positions to support claims.

## TEN GODS ANALYSIS
Interpret the three most prominent Ten Gods from the data. For each: name it, state which pillar it appears in, and give its psychological/life meaning for this specific Day Master. Note any absent Ten Gods and what that suggests.

## LUCK PILLAR (CURRENT DECADE)
Current luck pillar: ${bazi.luck_pillar_current}. State the element and polarity. How does it interact with the Day Master? Is this a supportive or challenging decade? What life domain is most activated? State the approximate age range.

## CLASH PATTERNS
${bazi.clash_patterns?.length ? `Address these clashes: ${bazi.clash_patterns.join(', ')}. For each: which pillars are involved, what domain of life it touches, how it typically manifests.` : 'No major clashes detected — note what this suggests about life flow.'}

## KEY THEMES
7–9 bullet points. Each must cite a specific pillar, stem, branch, or Ten God from the data. No generic astrology statements.

Output language: English. Tone: precise, analytical, no mystical language.`;

  return [{ json: {
    ...d,
    bazi_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 3000,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};

// return buildBaziPayload();   ← uncomment when using as standalone node


// ───────────────────────────────────────────────────────────────
//  NODE 2 — Build Numerology Classical Interpreter Payload
//  Paste into: n8n Code node "Build Numerology Interp Payload"
// ───────────────────────────────────────────────────────────────

const buildNumerologyPayload = () => {
  const d = $input.first().json;
  const num = d.numerology?.classical;

  if (!num) {
    return [{ json: { ...d, output_numerology: 'Numerology data unavailable' } }];
  }

  const prompt = `You are an expert in classical Pythagorean numerology.
The numbers have already been calculated. DO NOT recalculate. INTERPRET ONLY.
Every statement must reference a specific number from the data.

BIRTH DATA: ${d.name || 'Client'}, born ${d.birthdate}

PRE-CALCULATED NUMEROLOGY DATA:
${JSON.stringify(num, null, 2)}

INTERPRETATION INSTRUCTIONS:

## LIFE PATH ${num.life_path}
Core soul mission and life direction. What challenge and gift does this number encode? How does it express differently in youth vs. maturity? 3–4 sentences, specific to this number.

## DESTINY / EXPRESSION ${num.destiny}
How this person naturally moves through the world and what they are built to achieve outwardly. Tension or harmony with Life Path ${num.life_path}? 2–3 sentences.

## SOUL URGE ${num.soul_urge}
The inner motivator — what this person secretly needs to feel fulfilled. How does it conflict or align with the outward Destiny ${num.destiny}? 2–3 sentences.

## PERSONALITY ${num.personality}
How others perceive this person on first contact. Gap between inner Soul Urge ${num.soul_urge} and outer Personality ${num.personality} — note the tension if present.

## CURRENT CYCLE
Personal Year ${num.personal_year} — what chapter of the 9-year cycle is this, and what does it demand?
Personal Month ${num.personal_month} — what is the immediate focus within this year?
2–3 sentences total.

${num.karmic_debts?.length ? `## KARMIC DEBTS: ${num.karmic_debts.join(', ')}
State what each karmic debt number means as a specific recurring life challenge. Do not soften.` : ''}

## KEY THEMES
6–8 bullet points. Each references a specific number. No generic statements.

Output: English, precise, psychological depth.`;

  return [{ json: {
    ...d,
    numerology_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 2500,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ───────────────────────────────────────────────────────────────
//  NODE 3 — Build Matrix of Destiny (Ladini) Interpreter Payload
//  Paste into: n8n Code node "Build Matrix Interp Payload"
// ───────────────────────────────────────────────────────────────

const buildMatrixPayload = () => {
  const d = $input.first().json;
  const matrix = d.numerology?.matrix;

  if (!matrix) {
    return [{ json: { ...d, output_matrix: 'Matrix data unavailable' } }];
  }

  const prompt = `You are an expert in the Matrix of Destiny system (Natalya Ladini school).
The arcana positions have already been calculated. DO NOT recalculate. INTERPRET ONLY.
Every claim must reference the specific arcanum number from the data.

BIRTH DATA: ${d.name || 'Client'}, born ${d.birthdate}

PRE-CALCULATED MATRIX DATA:
${JSON.stringify(matrix, null, 2)}

The grid layout:
Row 0: [A, A+B, B]         — upper triangle (conscious)
Row 1: [A+C, CENTER, B+C]  — middle (integration)
Row 2: [C, D, B+D]         — lower triangle (karmic/unconscious)

INTERPRETATION INSTRUCTIONS:

## CORE (Arcanum ${matrix.core})
The central integration point of the personality. What is the deepest quality this person is working to embody? What does Arcanum ${matrix.core} demand and what does it offer? 3–4 sentences.

## MAIN TASK (Arcanum ${matrix.main_task})
The primary challenge and purpose in this lifetime. How does it manifest as recurring life situations? 2–3 sentences.

## COMFORT ZONE (Arcanum ${matrix.comfort_zone})
What this person defaults to when stressed or uncertain. Is it a strength or an escape? 2 sentences.

## HIGHER PURPOSE (Arcanum ${matrix.higher_purpose})
What this person is being called toward beyond personal fulfillment. 2 sentences.

## KARMIC TAIL [${matrix.karmic_tail?.join(', ')}]
The inherited karmic material. What patterns, fears, or gifts come from past cycles? Address each arcanum briefly. 3–4 sentences total.

${matrix.repeating_arcana?.length ? `## REPEATING ARCANA: ${matrix.repeating_arcana.join(', ')}
Amplified themes in this matrix. What does the repetition signal? 2 sentences.` : ''}

## KEY THEMES
6–8 bullet points. Each names a specific arcanum and its position.

Output: English, depth psychology register, no tarot clichés.`;

  return [{ json: {
    ...d,
    matrix_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 2500,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ───────────────────────────────────────────────────────────────
//  NODE 4 — Build Jyotish + Ayurveda Interpreter Payload
//  Paste into: n8n Code node "Build Jyotish Interp Payload"
// ───────────────────────────────────────────────────────────────

const buildJyotishPayload = () => {
  const d = $input.first().json;
  const jyotish = d.jyotish?.data || d.jyotish;

  if (!jyotish || jyotish.error) {
    return [{ json: { ...d, output_jyotish: `Jyotish data unavailable: ${jyotish?.error || 'no data'}` } }];
  }

  const timeSensitive = jyotish.time_sensitive
    ? 'NOTE: Birth time unknown — Ascendant and houses are unavailable. Analyse from Moon as Chandra Lagna.'
    : '';

  const prompt = `You are an expert Jyotish astrologer trained in classical Vedic interpretation.
All chart positions have been calculated. DO NOT recalculate. INTERPRET ONLY.
Reference specific planets, signs, houses, and nakshatras from the data in every claim.
${timeSensitive}

BIRTH DATA: ${d.name || 'Client'}, ${d.gender}, born ${d.birthdate} ${d.birthtime || ''}, ${d.birthplace}

PRE-CALCULATED JYOTISH DATA:
${JSON.stringify(jyotish, null, 2)}

INTERPRETATION INSTRUCTIONS:

## LAGNA / CHART FOUNDATION
${jyotish.time_sensitive ? 'Using Moon as Chandra Lagna (birth time unknown).' : `Ascendant: ${jyotish.ascendant?.sign} ${jyotish.ascendant?.degree?.toFixed(1)}°.`}
Describe the foundational life approach, physical constitution, and worldview this rising sign creates. 3 sentences.

## MOON — RASHI AND NAKSHATRA
Moon sign, degree, and nakshatra with pada. The nakshatra lord and its implications for mind, emotional patterns, and instinctive responses. This is the most important placement in Jyotish — give it depth. 4–5 sentences.

## SUN — SOUL DIRECTION
Sign, house, any key aspects from the data. What does this placement say about authority, father relationship, and life purpose expression? 2–3 sentences.

## KEY PLANETARY PLACEMENTS
Identify the 3 most significant placements from the data (planets in dignity, debility, own sign, or making prominent aspects). For each: state the planet, sign, house, and what this specifically means for this chart. 

## YOGAS DETECTED
${JSON.stringify(jyotish.yogas)}
Interpret each yoga. What does it promise and under what conditions does it activate? If no major yogas: note what this suggests.

## VIMSHOTTARI DASHA — CURRENT TIMING
Mahadasha: ${jyotish.dasha?.mahadasha} (${jyotish.dasha?.mahadasha_remaining_years} years remaining)
Antardasha: ${jyotish.dasha?.antardasha} (${jyotish.dasha?.antardasha_remaining_years} years remaining)
Interpret this mahadasha/antardasha combination: what domain of life is activated, what theme is being worked through, what is asked of the person right now? 4–5 sentences.

## AYURVEDIC CONSTITUTION
${JSON.stringify(jyotish.ayurveda)}
Translate dosha scores into practical implications: energy management, stress response, what environments and rhythms support this constitution. 2–3 sentences.

## KEY THEMES
7–9 bullet points. Each cites specific planet/sign/house/nakshatra from the data.

Output: English, classical Jyotish register, no Western astrology concepts.`;

  return [{ json: {
    ...d,
    jyotish_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 3500,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ───────────────────────────────────────────────────────────────
//  NODE 5 — Build Western Astrology (Greene/Arroyo) Interpreter Payload
//  Paste into: n8n Code node "Build Western Interp Payload"
// ───────────────────────────────────────────────────────────────

const buildWesternPayload = () => {
  const d = $input.first().json;
  const western = d.western?.data || d.western;

  if (!western || western.error) {
    return [{ json: { ...d, output_western: `Western data unavailable: ${western?.error || 'no data'}` } }];
  }

  // Filter to orb < 6° for key aspects
  const keyAspects = (western.aspects || [])
    .filter(a => a.orb <= 6 && ['sun','moon','mercury','venus','mars','jupiter','saturn'].includes(a.planet1))
    .slice(0, 12);

  const prompt = `You are a psychological astrologer trained in the traditions of Liz Greene and Stephen Arroyo.
All positions and aspects have been calculated. DO NOT recalculate. INTERPRET ONLY.
Ground every psychological insight in a specific placement or aspect from the data.

BIRTH DATA: ${d.name || 'Client'}, ${d.gender}, born ${d.birthdate} ${d.birthtime || ''}, ${d.birthplace}

PRE-CALCULATED WESTERN CHART DATA:
Ascendant: ${JSON.stringify(western.ascendant)}
MC: ${JSON.stringify(western.mc)}
Chart Ruler: ${western.chart_ruler}
Balance: ${JSON.stringify(western.balance)}
Planets: ${JSON.stringify(western.planets)}
Key Aspects (orb ≤ 6°): ${JSON.stringify(keyAspects)}

INTERPRETATION INSTRUCTIONS:

## CHART RULER — ${western.chart_ruler}
The chart ruler's sign and house from the data. This planet carries the entire chart's agenda. What psychological drive does it represent, and how does its placement modify the Ascendant's expression? 3 sentences.

## SUN — EGO STRUCTURE (Greene layer)
Sign, house, aspects from the data. Liz Greene frame: what myth or archetype is the Sun living? What does the ego need to feel whole? What is the core creative imperative? 3–4 sentences.

## MOON — EMOTIONAL BODY (Arroyo layer)
Sign, house, aspects. Arroyo frame: how does this person process emotion physically? What environmental conditions regulate the nervous system? What does the inner child need? 3–4 sentences.

## DOMINANT ELEMENT: ${western.balance?.elements ? Object.entries(western.balance.elements).sort((a,b)=>b[1]-a[1])[0][0] : 'Unknown'}
Count from data: ${JSON.stringify(western.balance?.elements)}
Psychological signature of this elemental dominance. What is overdeveloped? What is compensated for? What shadow does the absent/weak element create? 3 sentences.

## KEY ASPECTS — PSYCHOLOGICAL COMPLEXES
From the pre-calculated aspect list, interpret the 4–5 most significant aspects.
For each: name the two planets and aspect type, give the Greene/Arroyo psychological interpretation — what inner tension, gift, or wound does this create in lived experience? Avoid generic keywords.

## SATURN PLACEMENT
${western.planets?.saturn ? `Saturn: ${western.planets.saturn.sign}, House ${western.planets.saturn.house}, ${western.planets.saturn.retrograde ? 'retrograde' : 'direct'}.` : 'Saturn data unavailable.'}
Greene frame: the specific fear, the specific limitation, the specific domain where discipline is demanded and mastery becomes possible. 3 sentences.

## INDIVIDUATION THEME
Synthesise Sun + Moon + Saturn into one core psychological developmental theme. What is this person's individuation path in Jungian terms? 2–3 sentences.

## KEY THEMES
7–9 bullet points. Each cites a specific placement or aspect.

Output: English, depth psychology register. No cookbook astrology. No fortune-telling.`;

  return [{ json: {
    ...d,
    western_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 3000,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ───────────────────────────────────────────────────────────────
//  NODE 6 — Build Human Design Interpreter Payload
//  Paste into: n8n Code node "Build HD Interp Payload"
// ───────────────────────────────────────────────────────────────

const buildHDPayload = () => {
  const d = $input.first().json;
  const hd = d.human_design?.data || d.human_design;

  if (!hd || hd.error) {
    return [{ json: { ...d, output_hd: `HD data unavailable: ${hd?.error || 'no data'}` } }];
  }

  if (d.hd_skipped) {
    return [{ json: { ...d, output_hd: 'HD skipped: birth time required for accurate bodygraph calculation.' } }];
  }

  const prompt = `You are an expert Human Design analyst trained in the Ra Uru Hu system.
The bodygraph has already been calculated. DO NOT recalculate. INTERPRET ONLY.
Ground every insight in the specific type, profile, centers, channels, and gates from the data.

BIRTH DATA: ${d.name || 'Client'}, ${d.gender}, born ${d.birthdate} ${d.birthtime}, ${d.birthplace}

PRE-CALCULATED HUMAN DESIGN DATA:
Type: ${hd.type}
Strategy: ${hd.strategy}
Authority: ${hd.authority}
Profile: ${hd.profile}
Defined Centers: ${JSON.stringify(hd.defined_centers)}
Undefined Centers: ${JSON.stringify(hd.undefined_centers)}
Active Channels: ${JSON.stringify(hd.active_channels)}
Active Gates: ${JSON.stringify(hd.active_gates)}

INTERPRETATION INSTRUCTIONS:

## TYPE AND STRATEGY — ${hd.type}
What this type's energy dynamic means in practice — not the definition, the lived experience. How does "${hd.strategy}" specifically play out as daily decision-making? What happens when this strategy is ignored? 4 sentences.

## AUTHORITY — ${hd.authority}
The body's decision-making mechanism. Describe how this authority signal actually feels from the inside, what conditions it needs, and what overrides it. Practical, specific. 3 sentences.

## PROFILE — ${hd.profile}
The two lines, their themes, and how they interact as a life role. What archetype does this profile embody? What is its characteristic relationship to learning, community, and life purpose? 3–4 sentences.

## DEFINED CENTERS — ${hd.defined_centers?.join(', ') || 'None'}
For each defined center: what consistent energy or intelligence this gives — and what it projects onto others. Focus on the 2–3 most psychologically significant defined centers for this specific combination.

## UNDEFINED CENTERS — ${hd.undefined_centers?.join(', ') || 'None'}
For the 2–3 most significant undefined centers: what this person is conditioned by, what they amplify and return, and what wisdom they gain through this openness when not identified with it.

## KEY CHANNELS
${hd.active_channels?.length ? `Active channels: ${JSON.stringify(hd.active_channels)}
Interpret the 3 most significant channels. For each: what consistent gift or life theme it creates, how it expresses as personality, and what its shadow looks like.` : 'No complete channels — this creates a specific kind of openness. Interpret the hanging gate pattern and what it means for conditioning.'}

## KEY THEMES
7–9 bullet points. Each references a specific center, channel, gate, type, or profile from the data.

Output: English, HD system language. No astrology or numerology concepts mixed in.`;

  return [{ json: {
    ...d,
    hd_interp_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 3000,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ───────────────────────────────────────────────────────────────
//  NODE 7 — Build Lunar Calendar Interpreter Payload
//  Paste into: n8n Code node "Build Lunar Interp Payload"
//  Uses Claude Haiku — simple system, cheap, fast
// ───────────────────────────────────────────────────────────────

const buildLunarPayload = () => {
  const d = $input.first().json;
  const lunar = d.lunar;

  if (!lunar || lunar.error) {
    return [{ json: { ...d, output_lunar: `Lunar data unavailable: ${lunar?.error || 'no data'}` } }];
  }

  const prompt = `You are an expert in Vedic and Hellenistic lunar calendar traditions.
The lunar data has been pre-calculated. DO NOT recalculate. INTERPRET ONLY.
Reference every specific number and name from the data.

BIRTH DATA: ${d.name || 'Client'}, born ${d.birthdate}

PRE-CALCULATED LUNAR DATA:
${JSON.stringify(lunar, null, 2)}

INTERPRETATION INSTRUCTIONS:

## LUNAR DAY (TITHI) ${lunar.lunar_day} — ${lunar.paksha} PAKSHA
What is the energetic quality of being born on this tithi? The ${lunar.paksha} paksha (${lunar.paksha === 'Shukla' ? 'waxing' : 'waning'} phase) at ${lunar.illumination_percent}% illumination — what does this suggest about how this person relates to cycles, momentum, and completion? 3–4 sentences.

## BIRTH NAKSHATRA — ${lunar.nakshatra} (Pada ${lunar.pada})
The Moon's nakshatra at birth: its ruling deity, psychological quality, and characteristic gifts and shadows. Pada ${lunar.pada} — how does this quarter modify the nakshatra's expression? 4–5 sentences.

## SYNTHESIS
One short paragraph integrating the lunar day quality with the nakshatra. What does the combination say about this person's emotional rhythm and relationship to time?

Output: English, classical Vedic register. 3 sections only. No padding.`;

  return [{ json: {
    ...d,
    lunar_interp_payload: JSON.stringify({
      model: 'claude-haiku-4-5-20251001',
      max_tokens: 1200,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ═══════════════════════════════════════════════════════════════
//  NODE 8 — Updated SYNTHESIS (replaces Dialog 3)
//  Reads all 7 interpreter outputs.
//  Paste into: n8n Code node "Build Synthesis Payload"
// ═══════════════════════════════════════════════════════════════

const buildSynthesisPayload = () => {
  const d = $input.first().json;

  const prompt = `You are a senior analyst specializing in cross-system personality synthesis.
You do not practice any single tradition. Your role: identify what multiple independent systems 
AGREE on — treating convergence as signal, divergence as nuance.

You are working with interpreted outputs from 7 systems. Each has already been calculated and interpreted.
DO NOT re-interpret individual systems. SYNTHESISE ONLY.

=== BAZI INTERPRETATION ===
${d.output_bazi || 'unavailable'}

=== NUMEROLOGY (CLASSICAL) INTERPRETATION ===
${d.output_numerology || 'unavailable'}

=== MATRIX OF DESTINY INTERPRETATION ===
${d.output_matrix || 'unavailable'}

=== JYOTISH + AYURVEDA INTERPRETATION ===
${d.output_jyotish || 'unavailable'}

=== WESTERN ASTROLOGY INTERPRETATION ===
${d.output_western || 'unavailable'}

=== HUMAN DESIGN INTERPRETATION ===
${d.output_hd || 'unavailable'}

=== LUNAR CALENDAR INTERPRETATION ===
${d.output_lunar || 'unavailable'}

SYNTHESIS INSTRUCTIONS:

## CONVERGENCE MAP
Identify every theme, trait, tension, or gift appearing in TWO OR MORE systems.
For each: name the theme, list which systems confirm it, rate strength (STRONG = 3+ systems / MODERATE = 2 systems), one practical sentence. Minimum 8 convergent themes.

## BOTTLENECKS
4–5 most significant self-limiting patterns confirmed by multiple systems. For each:
- Clear name (no esoteric terminology)
- Which systems flag it and how
- How it manifests in daily life
- Root dynamic in one sentence

## POWER SOURCES
4–5 most significant innate strengths confirmed by multiple systems. For each:
- Clear name
- Which systems confirm it
- Specific activation condition
- What suppression looks like

## STRATEGIC VECTOR
CORE LIFE THEME: 2–3 sentences, no jargon.
CURRENT PHASE: Synthesise BaZi luck pillar + Jyotish dasha + Numerology personal year. 
Is this expansion / consolidation / transition / harvest? Be specific.
OPTIMAL DIRECTION: specific environments, roles, and approaches — not job titles.

## SINGLE-SYSTEM SIGNALS
Themes from only ONE system strong enough to note. Label each with source. Mark as hypotheses.

## TIME-SENSITIVE FLAGS
Any elements that were marked time-sensitive due to unknown birth time. 
Significance: HIGH / MEDIUM / LOW.

Output language: English. Tone: precise, direct, no mystical language, no flattery.`;

  return [{ json: {
    ...d,
    dialog3_payload: JSON.stringify({
      model: 'deepseek-chat',
      max_tokens: 6000,
      messages: [{ role: 'user', content: prompt }]
    })
  }}];
};


// ═══════════════════════════════════════════════════════════════
//  SAVE OUTPUT NODES — pattern for each interpreter
//  Duplicate this for each system, changing field names.
// ═══════════════════════════════════════════════════════════════

/*
After each HTTP Request node (DeepSeek/Anthropic API call),
add a Code node to extract the response:

// Save BaZi Output (adjust field names per system):
const response = $input.first().json;
const output_bazi = response.choices?.[0]?.message?.content || '';
const prev = $('Build BaZi Interp Payload').item.json;
return [{ json: { ...prev, output_bazi } }];

// For Anthropic (Haiku lunar):
const response = $input.first().json;
const output_lunar = response.content?.[0]?.text || '';
const prev = $('Build Lunar Interp Payload').item.json;
return [{ json: { ...prev, output_lunar } }];
*/


// ═══════════════════════════════════════════════════════════════
//  N8N WORKFLOW WIRING GUIDE
// ═══════════════════════════════════════════════════════════════

/*
CALCULATION LAYER (parallel branches):
  ├── Code: BaZi Calculator          → saves d.bazi
  ├── Code: Numerology Calculator    → saves d.numerology
  ├── Code: Lunar Calculator         → saves d.lunar
  └── Code: Astrology Service Node   → saves d.jyotish, d.western, d.human_design
              ↓
  Merge Node (mode: "Merge by Position" or pass through if sequential)
              ↓
INTERPRETATION LAYER (sequential — simplest in n8n without parallel branching):
  Code: Build BaZi Interp Payload
  HTTP: DeepSeek API
  Code: Save output_bazi
              ↓
  Code: Build Numerology Interp Payload
  HTTP: DeepSeek API
  Code: Save output_numerology
              ↓
  Code: Build Matrix Interp Payload
  HTTP: DeepSeek API
  Code: Save output_matrix
              ↓
  Code: Build Jyotish Interp Payload
  HTTP: DeepSeek API
  Code: Save output_jyotish
              ↓
  Code: Build Western Interp Payload
  HTTP: DeepSeek API
  Code: Save output_western
              ↓
  Code: Build HD Interp Payload
  HTTP: DeepSeek API
  Code: Save output_hd
              ↓
  Code: Build Lunar Interp Payload
  HTTP: Anthropic API (Haiku)
  Code: Save output_lunar
              ↓
SYNTHESIS:
  Code: Build Synthesis Payload      → reads all output_* fields
  HTTP: DeepSeek API
  Code: Save output3
              ↓
OUTPUT (Dialog 4 — unchanged from v4):
  Code: Build Dialog 4 Payload       → reads output3, client fields
  HTTP: Anthropic API (Claude Sonnet)
  Code: Extract doc_client
              ↓
  Code: Build Passport Payload       → reads doc_client
  HTTP: Anthropic API (Haiku)
  Code: Extract doc_passport
              ↓
  Telegram: Send doc + passport

API ENDPOINTS:
  DeepSeek: POST https://api.deepseek.com/v1/chat/completions
    Body: {{ $json.bazi_interp_payload }}  (or relevant field)
    Auth: deepSeekApi credential
    Timeout: 60000

  Anthropic (Haiku): POST https://api.anthropic.com/v1/messages
    Headers: x-api-key, anthropic-version: 2023-06-01
    Body: {{ $json.lunar_interp_payload }}
    Timeout: 30000
*/

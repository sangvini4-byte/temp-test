"""
Blueprint Pipeline v5 → v6: Domain-Partitioned Synthesis + Multi-File Delivery
═══════════════════════════════════════════════════════════════════════════

ЧТО МЕНЯЕТСЯ:

УДАЛЯЕТСЯ (избыточно после рефакторинга):
  - старая цепочка синтеза (Build Synthesis Payload → Dialog—Synthesis(DeepSeek)
    → Save Output3 → Update Sheets—Synthesis) — заменяется на доменный синтез
  - старая цепочка единого клиентского документа (Build Dialog 4 Payload →
    Dialog 4 Client Document → Extract → Update Sheets → Build Passport →
    Dialog 4b → Extract Passport → Prepare Document File → Send Client Doc →
    Send Passport → Update Status) — больше не нужна, заменяется 6 файлами
  - 4 параллельные самостоятельные ветки Timing/Career/Relational/Intimacy,
    добавленные в прошлых итерациях — они дублировали работу синтеза,
    обращаясь к сырым данным напрямую. Теперь их функция поглощена
    доменным синтезом, а "writer" слой (Claude, тёплый русский текст)
    читает уже готовый, расчленённый по доменам материал.

ДОБАВЛЯЕТСЯ:

  Merge Interpretation Results
        │
  Build Domain Synthesis Payload  (Code)
        │   собирает: 7 интерпретаций + точные сырые факты
        │   (дashы/даты, дома, кланы, спаусс-палас, HD-центры) —
        │   те же вычисления, что раньше делали отдельные ветки,
        │   но теперь как ВХОД для единого синтеза, а не отдельные вызовы
        ▼
  Dialog — Domain Synthesis (Claude Sonnet)
        │   ОДИН вызов. System prompt жёстко требует:
        │   "каждый инсайт принадлежит ровно одному домену;
        │    если применим к нескольким — присвой одному,
        │    в остальных дай однострочную ссылку 'см. [Домен]'"
        │   Output: 7 секций с явными маркерами
        │   === FRONTEND === ... === BACKEND === ... === COMPASS ===
        ▼
  Parse Domain Synthesis  (Code — regex-split по маркерам)
        │
        ├──────────┬──────────┬──────────┬──────────┬──────────┐
        ▼          ▼          ▼          ▼          ▼          ▼
     Frontend   Backend    Timing    Relations   Career   [IF opt-in]
     Writer     Writer     Writer    Writer      Writer    Intimacy Writer
     (Claude)   (Claude)   (Claude)  (Claude)    (Claude)   (Claude)
        │          │          │          │          │          │
      .txt       .txt       .txt       .txt       .txt       .txt
        │          │          │          │          │          │
     Telegram   Telegram   Telegram   Telegram   Telegram   Telegram
                                                                  
  + отдельно: Compass Writer (Claude Haiku) → читает только домен COMPASS
    → ОДНО сообщение (не файл) с предельно сжатым "техпаспортом"

ВАЖНО ПРО КЭШ:
  Старая логика кэша резолвила ОДИН файл (doc_client). Теперь файлов 6+1,
  и подмена устаревшего кэша рискует рассинхронизировать домены между
  собой (ровно то противоречие, которого мы избегаем доменной партицией).
  Поэтому: при cache_hit мы НЕ переотправляем старые файлы — просто
  предупреждаем клиента и пересчитываем заново. Это сознательный trade-off:
  дороже по токенам при повторных запросах, но гарантирует согласованность
  между всеми 6 файлами. Если кэш важен — можно вернуться к этому позже,
  сохраняя domain_synthesis целиком в Sheets и кэшируя именно его (а не
  финальные written-файлы), тогда writer-слой можно перезапускать дёшево.
"""
import json

SRC = '/home/claude/Blueprint_Pipeline_v5.json'
DST = '/home/claude/Blueprint_Pipeline_v6.json'

wf = json.load(open(SRC))
nodes = wf['nodes']
conns = wf['connections']
by_name = {n['name']: n for n in nodes}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 0 — helpers
# ═══════════════════════════════════════════════════════════════════════════

def code_node(node_id, name, js, x, y):
    return {"parameters": {"jsCode": js.strip()}, "id": node_id, "name": name,
            "type": "n8n-nodes-base.code", "typeVersion": 2, "position": [x, y]}

def claude_http(node_id, name, payload_field, x, y, timeout=150000):
    return {
        "parameters": {
            "method": "POST", "url": "https://api.anthropic.com/v1/messages",
            "sendHeaders": True,
            "headerParameters": {"parameters": [
                {"name": "x-api-key", "value": "={{ $env.ANTHROPIC_API_KEY }}"},
                {"name": "anthropic-version", "value": "2023-06-01"},
                {"name": "content-type", "value": "application/json"},
            ]},
            "sendBody": True, "contentType": "raw", "rawContentType": "application/json",
            "body": f"={{{{ $json.{payload_field} }}}}", "options": {"timeout": timeout},
        },
        "id": node_id, "name": name, "type": "n8n-nodes-base.httpRequest",
        "typeVersion": 4.2, "position": [x, y],
    }

def if_node(node_id, name, left_expr, x, y):
    return {
        "parameters": {"conditions": {
            "options": {"caseSensitive": False, "leftValue": "", "typeValidation": "strict"},
            "conditions": [{"id": "c1", "leftValue": left_expr, "rightValue": True,
                            "operator": {"type": "boolean", "operation": "equal"}}],
            "combinator": "and"}, "options": {}},
        "id": node_id, "name": name, "type": "n8n-nodes-base.if",
        "typeVersion": 2, "position": [x, y],
    }

def sheets_update(node_id, name, field, x, y):
    return {
        "parameters": {
            "operation": "update",
            "documentId": {"__rl": True, "value": "1qR5uLC4deAyCr5plpMtj4JwqQyXDKQpTRZ4kOL99kPQ", "mode": "id"},
            "sheetName": {"__rl": True, "value": "Clients", "mode": "name"},
            "columns": {
                "mappingMode": "defineBelow",
                "value": {field: f"={{{{ $json.{field} }}}}", "status": f"{field}_done"},
                "matchingColumns": ["user_id"],
                "schema": [
                    {"id": "user_id", "displayName": "user_id", "required": False, "defaultMatch": True,
                     "display": True, "type": "string", "canBeUsedToMatch": True},
                    {"id": field, "displayName": field, "required": False, "defaultMatch": False,
                     "display": True, "type": "string", "canBeUsedToMatch": False},
                    {"id": "status", "displayName": "status", "required": False, "defaultMatch": False,
                     "display": True, "type": "string", "canBeUsedToMatch": False},
                ],
            }, "options": {},
        },
        "id": node_id, "name": name, "type": "n8n-nodes-base.googleSheets",
        "typeVersion": 4.2, "position": [x, y],
        "credentials": {"googleSheetsOAuth2Api": {"id": "YVApJWjSbMBLEzBo", "name": "Google Sheets OAuth2 API"}},
    }

def prepare_file_js(field, label):
    safe_label = label.replace(' ', '_')
    return f"""
const d = $input.first().json;
const text = `${{d.name}}. {label}\\n\\n${{d.{field} || ''}}`;
const binary = Buffer.from(text, 'utf8').toString('base64');
return [{{
  json: {{ ...d }},
  binary: {{ data: {{ data: binary, mimeType: 'text/plain',
    fileName: `${{d.name}}_{safe_label}.txt`, fileExtension: 'txt' }} }}
}}];
"""

def telegram_send_doc(node_id, name, x, y):
    return {
        "parameters": {"operation": "sendDocument", "chatId": "={{ $json.chat_id }}",
                       "binaryData": True, "additionalFields": {}},
        "id": node_id, "name": name, "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2, "position": [x, y],
        "credentials": {"telegramApi": {"id": "rTQk3qLI5Cjv96lt", "name": "Telegram account 2"}},
    }

def telegram_send_text(node_id, name, text_expr, x, y):
    return {
        "parameters": {"chatId": "={{ $json.chat_id }}", "text": text_expr,
                       "additionalFields": {"parse_mode": "Markdown"}},
        "id": node_id, "name": name, "type": "n8n-nodes-base.telegram",
        "typeVersion": 1.2, "position": [x, y],
        "credentials": {"telegramApi": {"id": "rTQk3qLI5Cjv96lt", "name": "Telegram account 2"}},
    }

def remove_node_chain(*names):
    """Remove nodes by name and any connection entries referencing them
    (as source key or as a target inside any branch)."""
    removed = set(names)
    nodes[:] = [n for n in nodes if n['name'] not in removed]
    for key in list(conns.keys()):
        if key in removed:
            del conns[key]
            continue
        for branch in conns[key].get('main', []):
            branch[:] = [link for link in branch if link.get('node') not in removed]

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 1 — remove redundant old branches
# ═══════════════════════════════════════════════════════════════════════════

remove_node_chain(
    # old single-blob synthesis (DeepSeek)
    "Build Synthesis Payload", "Dialog — Synthesis (DeepSeek)",
    "Save Output3 (Synthesis)", "Update Sheets — Synthesis",
    # old single client document + passport
    "Build Dialog 4 Payload", "Dialog 4 — Client Document (Claude Sonnet)",
    "Extract Doc Client", "Update Sheets — DOC CLIENT",
    "Build Passport Payload", "Dialog 4b — Passport (Claude Haiku)",
    "Extract Passport", "Prepare Document File",
    "Telegram — Send Client Doc", "Telegram — Send Passport",
    "Update Status in Sheets",
    # old standalone domain branches — superseded by domain-partitioned synthesis
    "Build Timing Payload", "Dialog — Timing & Prognosis (Claude Sonnet)",
    "Save Output — Timing & Prognosis", "Update Sheets — Timing",
    "Prepare Timing Document File", "Telegram — Send Timing Document",
    "Build Career Payload", "Dialog — Career & Place Fit (Claude Sonnet)",
    "Save Output — Career & Place Fit", "Update Sheets — Career",
    "Prepare Career Document File", "Telegram — Send Career Document",
    "Build Relational Profile Payload", "Dialog — Relational Profile (Claude Sonnet)",
    "Save Output — Relational Profile", "Update Sheets — Relational",
    "Prepare Relational Document File", "Telegram — Send Relational Document",
    "Check Intimacy Opt-In", "IF: Intimacy Opt-In?", "Build Intimacy Payload",
    "Dialog — Intimacy Analysis (Claude Sonnet)", "Save Output — Intimacy Analysis",
    "Update Sheets — Intimacy", "Prepare Intimacy Document File", "Telegram — Send Intimacy Document",
)

by_name = {n['name']: n for n in nodes}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 2 — patch cache logic (now keyed on domain_synthesis, not doc_client)
# ═══════════════════════════════════════════════════════════════════════════

check_cache_node = by_name['Check Cache']
check_cache_node['parameters']['jsCode'] = r"""
// ══════════════════════════════════════════════════════════════
//  Кэш теперь информационный, а не "skip-and-resend".
//  Резолвить 6 отдельных файлов из старого кэша рискует рассинхронизировать
//  домены между собой — ровно то противоречие, которого мы избегаем доменным
//  синтезом. Поэтому: если есть кэш — предупреждаем клиента, но пересчитываем
//  заново, гарантируя согласованность всех 6 файлов между собой.
// ══════════════════════════════════════════════════════════════
const lookup = $input.first().json;
const prev = $('Validate Input').item.json;

const cacheHit = !!(lookup && lookup.domain_synthesis && lookup.domain_synthesis.length > 100);

return [{ json: { ...prev, cache_hit: cacheHit } }];
""".strip()

# IF: Cache Hit? now just informs, both branches continue into the same
# pipeline — true branch sends a heads-up message first.
cache_notify_node = by_name['Telegram — Cache Notify']
cache_notify_node['parameters']['text'] = (
    "🔄 У меня уже был анализ для *{{ $json.name }}* ({{ $json.birthdate }}), "
    "но я пересчитываю заново — это гарантирует, что все файлы (характер, "
    "структура, тайминг, отношения, карьера) будут согласованы между собой.\n\n"
    "Займёт около 15–20 минут."
)

# Re-route both branches of "IF: Cache Hit?" into "Save to Sheets" (continue
# the pipeline either way). True branch goes through the notify message first.
conns["IF: Cache Hit?"] = {"main": [
    [{"node": "Telegram — Cache Notify", "type": "main", "index": 0}],
    [{"node": "Save to Sheets", "type": "main", "index": 0}],
]}
conns["Telegram — Cache Notify"] = {"main": [[{"node": "Save to Sheets", "type": "main", "index": 0}]]}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 3 — Build Domain Synthesis Payload (Claude Sonnet, ONE call)
# ═══════════════════════════════════════════════════════════════════════════

X0, Y0, STEP = 4840, 420, 220

domain_synthesis_build_js = r"""
// ══════════════════════════════════════════════════════════════
//  "Build Domain Synthesis Payload"
//  ОДИН вызов Claude Sonnet, заменяющий: старый общий синтез (DeepSeek)
//  И четыре отдельные ветки (Timing/Career/Relational/Intimacy), которые
//  раньше дублировали работу, обращаясь к сырым данным напрямую.
//
//  Здесь мы СОБИРАЕМ точные сырые факты (даты дash, дома, спаусс-палас,
//  HD-центры — те же вычисления, что раньше жили в отдельных билдерах)
//  И передаём их вместе с 7 интерпретациями в один промпт.
//  Модель партиционирует материал на 6 доменов + компас, явно помечая
//  границы маркерами, и придерживается правила "один инсайт — один домен".
// ══════════════════════════════════════════════════════════════

const d = $input.first().json;
const jy = d.jyotish, bz = d.bazi, hd = d.human_design, num = d.numerology?.classical;

// ── precise facts: career (10th/6th house) ──────────────────────────────
const SIGN_LORD = {0:'mars',1:'venus',2:'mercury',3:'moon',4:'sun',5:'mercury',
  6:'venus',7:'mars',8:'jupiter',9:'saturn',10:'saturn',11:'jupiter'};
function houseOf(signIdx, ascIdx) { return ((signIdx - ascIdx + 12) % 12) + 1; }
const ascIdx = jy?.ascendant?.sign_index ?? null;

let tenthHouseLord = null, sixthHouseLord = null, seventhHouseLord = null, eighthHouseLord = null;
let tenthHousePlanets = [], seventhHousePlanets = [];
if (ascIdx !== null) {
  tenthHouseLord   = SIGN_LORD[(ascIdx + 9) % 12];
  sixthHouseLord   = SIGN_LORD[(ascIdx + 5) % 12];
  seventhHouseLord = SIGN_LORD[(ascIdx + 6) % 12];
  eighthHouseLord  = SIGN_LORD[(ascIdx + 7) % 12];
  tenthHousePlanets = Object.entries(jy.planets || {})
    .filter(([,v]) => v?.sign_index !== undefined && houseOf(v.sign_index, ascIdx) === 10)
    .map(([k]) => k);
  seventhHousePlanets = Object.entries(jy.planets || {})
    .filter(([,v]) => v?.sign_index !== undefined && houseOf(v.sign_index, ascIdx) === 7)
    .map(([k]) => k);
}

// ── precise facts: Bazi dominant element + spouse palace ────────────────
const STEM_ELEMENT = {Jia:'Wood',Yi:'Wood',Bing:'Fire',Ding:'Fire',Wu:'Earth',Ji:'Earth',
  Geng:'Metal',Xin:'Metal',Ren:'Water',Gui:'Water'};
const BRANCH_ELEMENT = {Zi:'Water',Chou:'Earth',Yin:'Wood',Mao:'Wood',Chen:'Earth',Si:'Fire',
  Wu:'Fire',Wei:'Earth',Shen:'Metal',You:'Metal',Xu:'Earth',Hai:'Water'};
let dominantElement = null;
if (bz) {
  const counts = {};
  const allStems = [bz.year_pillar?.stem, bz.month_pillar?.stem, bz.day_pillar?.stem, bz.hour_pillar?.stem,
    ...Object.values(bz.hidden_gods || {}).flat().filter(Boolean).map(h => h.stem)].filter(Boolean);
  for (const s of allStems) { const e = STEM_ELEMENT[s]; if (e) counts[e] = (counts[e] || 0) + 1; }
  dominantElement = Object.entries(counts).sort((a, b) => b[1] - a[1])[0]?.[0] || null;
}
const spousePalace = bz?.day_pillar?.branch || null;
const spousePalaceElement = spousePalace ? BRANCH_ELEMENT[spousePalace] : null;
const spouseClashes = (bz?.clash_patterns || []).filter(c => c.toLowerCase().includes('day'));

// ── precise facts: relational (Rahu/Ketu/Venus/Mars houses) ─────────────
const rahu = jy?.planets?.north_node, ketu = jy?.planets?.south_node;
const venus = jy?.planets?.venus, mars = jy?.planets?.mars;
const venusHouse = (venus && ascIdx !== null) ? houseOf(venus.sign_index, ascIdx) : null;
const marsHouse  = (mars  && ascIdx !== null) ? houseOf(mars.sign_index, ascIdx)  : null;
const rahuHouse  = (rahu  && ascIdx !== null) ? houseOf(rahu.sign_index, ascIdx)  : null;
const ketuHouse  = (ketu  && ascIdx !== null) ? houseOf(ketu.sign_index, ascIdx)  : null;

// ── precise facts: HD somatic centers ────────────────────────────────────
const definedCenters = hd?.defined_centers || [];
const sacralDefined = definedCenters.includes('sacral');
const solarPlexusDefined = definedCenters.includes('solar_plexus');
const heartDefined = definedCenters.includes('heart');

// ── current-date Bazi (year/month pillar TODAY, for timing) ─────────────
const BASE_URL = 'http://astrology:8000';
const today = new Date();
const todayIso = today.toISOString().slice(0, 10);
const genderMap = { 'мужской': 'male', 'женский': 'female' };
const genderEn = genderMap[d.gender] || 'male';

let currentBazi = null, error_current_bazi = null;
if (d.lon !== null && d.lon !== undefined) {
  try {
    const res = await fetch(`${BASE_URL}/bazi`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        birth_date: todayIso, birth_time: '12:00',
        timezone: Number(d.tz_offset ?? 0),
        latitude: d.lat ?? null, longitude: d.lon ?? null, gender: genderEn,
      }),
    });
    if (res.ok) currentBazi = await res.json();
    else error_current_bazi = `HTTP ${res.status}`;
  } catch (e) { error_current_bazi = e.message; }
} else {
  error_current_bazi = 'longitude unavailable';
}

function reduceToMaster(n) {
  if (n === 11 || n === 22 || n === 33) return n;
  while (n > 9) {
    let s = 0, x = n;
    while (x > 0) { s += x % 10; x = Math.floor(x / 10); }
    n = s;
    if (n === 11 || n === 22 || n === 33) return n;
  }
  return n;
}
const personalDay = (num?.personal_month !== undefined)
  ? reduceToMaster(num.personal_month + today.getDate()) : null;

const intimacyOptIn = d.intimacy_opt_in === true;

const intimacyDomainSpec = intimacyOptIn ? `
=== INTIMACY ===
Seven-layer intimacy analysis (psychological, somatic, archetypal — never explicit):
intimacy blueprint (Venus/Mars + HD centers as felt body experience), attraction-vs-compatibility
gap restated through an intimacy lens (may briefly cross-reference RELATIONS, don't fully repeat it),
shadow material (8th house + undefined centers), somatic layer (sacral/solar-plexus/heart specifics
below), three partner archetypes through an intimacy lens, karmic loop in intimate contexts,
timing overlay for intimacy specifically. ~1200-1500 words.
` : '';

const prompt = `You are a senior analyst performing DOMAIN-PARTITIONED SYNTHESIS across seven
independently-interpreted esoteric systems (BaZi, Numerology classical, Matrix of Destiny,
Jyotish, Western psychological astrology, Human Design, Lunar calendar) plus precomputed
precise facts. Your job is NOT a single blended summary — it is to sort all material into
SIX (or seven, if intimacy is requested) STRICTLY SEPARATE domains that will later become
six separate documents read independently by the client.

CRITICAL RULE — NO OVERLAP, NO CONTRADICTION:
Every insight, pattern, or claim belongs to EXACTLY ONE domain. Before placing something,
ask: "which single domain owns this?" If a pattern is genuinely relevant to two domains,
write it fully in the domain it belongs to MOST, and in the other domain write only a
one-line cross-reference: "(see ХАРАКТЕР for the underlying pattern)" — never restate the
same claim with different wording in two places. This is the single most important
instruction in this task: downstream, each domain becomes an independent file the client
reads in isolation, days apart — duplication reads as repetition, and any subtle wording
drift between two domains describing "the same thing" reads as CONTRADICTION. Do not let
that happen.

OUTPUT FORMAT — use these exact markers, each on its own line, nothing else on that line:

=== FRONTEND ===
(Answers "who am I?" — the visible, socially-expressed personality: energy type and how it
reads to others, communication style, natural strengths in action, the "business card" version
of this person. Frontend = how they show up. ~700-900 words.)

=== BACKEND ===
(Answers "how am I built?" — the internal psychological architecture invisible from outside:
structural bottlenecks (root dynamics, not symptoms), power sources and their activation
conditions, the shadow material, what costs what. Backend = the mechanism underneath.
~700-900 words.)

=== TIMING ===
(90-day window + longer arc. Use: current dasha/antardasha (mahadasha=${JSON.stringify(jy?.dasha?.current_mahadasha)},
antardasha=${JSON.stringify(jy?.dasha?.current_antardasha)}), natal Bazi luck pillar
(${JSON.stringify(bz?.luck_pillar)}), TODAY's Bazi year/month pillar (${JSON.stringify(currentBazi?.year_pillar)} /
${JSON.stringify(currentBazi?.month_pillar)}) against natal day master (${JSON.stringify(bz?.day_master)}) —
does it support, clash, or drain? Personal year ${num?.personal_year}, personal month
${num?.personal_month}, personal day ${personalDay}. Break into 3 monthly segments with
high-confidence windows and friction windows where systems align/diverge. Be honest about
difficult periods. ~900-1100 words.)

=== RELATIONS ===
(Attraction vs compatibility gap — THE most important relational insight, name it explicitly:
attraction from Rahu house ${rahuHouse}, 8th house lord ${eighthHouseLord}, Mars house ${marsHouse};
compatibility from 7th house lord ${seventhHouseLord} (${JSON.stringify(seventhHousePlanets)} present),
Bazi spouse palace ${spousePalace}/${spousePalaceElement}${spouseClashes.length ? `, clash: ${JSON.stringify(spouseClashes)}` : ''}.
Three partner archetypes (Mirror/Teacher/Home). Karmic loop via Ketu house ${ketuHouse} / Rahu house
${rahuHouse}. Relational timing window in next 12-24mo. ~900-1100 words.)

=== CAREER ===
(Vocational blueprint from HD type/strategy/profile (${hd?.type}, ${hd?.strategy}, ${hd?.profile})
+ Jyotish 10th house lord ${tenthHouseLord} (planets present: ${JSON.stringify(tenthHousePlanets)}) +
life path ${num?.life_path}. Working style from Bazi dominant element ${dominantElement} +
HD definition. Authority/leadership style from HD authority ${hd?.authority}. Structural
challenges from HD undefined centers + 6th house lord ${sixthHouseLord} + any karmic debt
numbers (${JSON.stringify(num?.karmic_debts)}). Environment/place fit from dominant element
${dominantElement}. Current timing verdict for career moves. ~900-1100 words.)
${intimacyDomainSpec}
=== COMPASS ===
(MAXIMUM 180 words. Three short blocks: КАК УСТРОЕН(А) / ЧТО ТОРМОЗИТ / ОТКУДА СИЛА —
2-3 lines each, distilled to the single sharpest claim per block, drawn from BACKEND.
This becomes a standalone short message, not a file — ruthlessly compressed, zero padding.)

=== END ===

SOURCE MATERIAL — seven independent system interpretations (already computed, do not
recalculate astrology/numerology/HD from scratch, only synthesise):

--- BAZI ---
${d.output_bazi || 'unavailable'}

--- NUMEROLOGY (CLASSICAL) ---
${d.output_numerology || 'unavailable'}

--- MATRIX OF DESTINY ---
${d.output_matrix || 'unavailable'}

--- JYOTISH ---
${d.output_jyotish || 'unavailable'}

--- WESTERN ASTROLOGY ---
${d.output_western || 'unavailable'}

--- HUMAN DESIGN ---
${d.output_hd || 'unavailable'}

--- LUNAR CALENDAR ---
${d.output_lunar || 'unavailable'}

ADDITIONAL PRECISE FACTS (computed, not interpreted — use these for specificity in TIMING/
CAREER/RELATIONS/INTIMACY rather than inventing dates or houses):
HD somatic centers: sacral_defined=${sacralDefined}, solar_plexus_defined=${solarPlexusDefined}, heart_defined=${heartDefined}
${error_current_bazi ? `NOTE: current-date Bazi pillar unavailable (${error_current_bazi}) — work from natal luck pillar + dasha only for TIMING.` : ''}
${ascIdx === null ? 'NOTE: Ascendant unknown (birth time not provided) — house-dependent claims in CAREER/RELATIONS are TIME-SENSITIVE; flag accordingly rather than inventing house placements.' : ''}

${intimacyOptIn ? 'INTIMACY DOMAIN REQUESTED — client opted in. Include the === INTIMACY === section with full depth, never explicit content.' : 'INTIMACY DOMAIN NOT REQUESTED — omit the === INTIMACY === marker and section entirely.'}

Output language for this synthesis: English, analytical register (the warmth/Russian
translation happens in a later step per domain — this stage is structural, not emotional).
Tone: precise, direct, no mystical language, no flattery, no hedging on difficult material.`;

return [{ json: {
  ...d,
  current_bazi: currentBazi, error_current_bazi, personal_day: personalDay,
  domain_synthesis_payload: JSON.stringify({
    model: 'claude-sonnet-4-20250514', max_tokens: 8000,
    messages: [{ role: 'user', content: prompt }]
  })
}}];
"""

domain_synthesis_save_js = r"""
const response = $input.first().json;
const domain_synthesis = response.content?.[0]?.text || '';
const prev = $('Build Domain Synthesis Payload').item.json;
return [{ json: { ...prev, domain_synthesis } }];
"""

# Parse the marker-delimited output into 7 (6 unconditional + compass) fields.
parse_domains_js = r"""
// ══════════════════════════════════════════════════════════════
//  "Parse Domain Synthesis"
//  Splits the single Claude Sonnet response into separate domain fields
//  using the === MARKER === delimiters defined in the synthesis prompt.
// ══════════════════════════════════════════════════════════════

const d = $input.first().json;
const text = d.domain_synthesis || '';

const MARKERS = ['FRONTEND', 'BACKEND', 'TIMING', 'RELATIONS', 'CAREER', 'INTIMACY', 'COMPASS', 'END'];

function extract(marker, nextMarkers) {
  const startRe = new RegExp(`===\\s*${marker}\\s*===`, 'i');
  const startMatch = text.match(startRe);
  if (!startMatch) return '';
  const startIdx = startMatch.index + startMatch[0].length;

  let endIdx = text.length;
  for (const nm of nextMarkers) {
    const endRe = new RegExp(`===\\s*${nm}\\s*===`, 'i');
    const endMatch = text.slice(startIdx).match(endRe);
    if (endMatch) {
      endIdx = startIdx + endMatch.index;
      break;
    }
  }
  return text.slice(startIdx, endIdx).trim();
}

const synth_frontend  = extract('FRONTEND',  ['BACKEND','TIMING','RELATIONS','CAREER','INTIMACY','COMPASS','END']);
const synth_backend   = extract('BACKEND',   ['TIMING','RELATIONS','CAREER','INTIMACY','COMPASS','END']);
const synth_timing    = extract('TIMING',    ['RELATIONS','CAREER','INTIMACY','COMPASS','END']);
const synth_relations = extract('RELATIONS', ['CAREER','INTIMACY','COMPASS','END']);
const synth_career    = extract('CAREER',    ['INTIMACY','COMPASS','END']);
const synth_intimacy  = extract('INTIMACY',  ['COMPASS','END']);
const synth_compass   = extract('COMPASS',   ['END']);

const parse_warnings = [];
if (!synth_frontend)  parse_warnings.push('FRONTEND marker not found or empty');
if (!synth_backend)   parse_warnings.push('BACKEND marker not found or empty');
if (!synth_timing)    parse_warnings.push('TIMING marker not found or empty');
if (!synth_relations) parse_warnings.push('RELATIONS marker not found or empty');
if (!synth_career)    parse_warnings.push('CAREER marker not found or empty');
if (!synth_compass)   parse_warnings.push('COMPASS marker not found or empty');
if (d.intimacy_opt_in === true && !synth_intimacy) parse_warnings.push('INTIMACY requested but marker not found or empty');

return [{ json: {
  ...d,
  synth_frontend, synth_backend, synth_timing, synth_relations, synth_career,
  synth_intimacy, synth_compass, parse_warnings,
}}];
"""

nodes += [
    code_node("build-domain-synth", "Build Domain Synthesis Payload",
              domain_synthesis_build_js, X0, Y0),
    claude_http("http-domain-synth", "Dialog — Domain Synthesis (Claude Sonnet)",
                "domain_synthesis_payload", X0 + STEP, Y0, timeout=180000),
    code_node("save-domain-synth", "Save Output — Domain Synthesis",
              domain_synthesis_save_js, X0 + 2 * STEP, Y0),
    sheets_update("sheets-domain-synth", "Update Sheets — Domain Synthesis",
                  "domain_synthesis", X0 + 3 * STEP, Y0),
    code_node("parse-domains", "Parse Domain Synthesis",
              parse_domains_js, X0 + 4 * STEP, Y0),
]

conns["Build Domain Synthesis Payload"] = {"main": [[{"node": "Dialog — Domain Synthesis (Claude Sonnet)", "type": "main", "index": 0}]]}
conns["Dialog — Domain Synthesis (Claude Sonnet)"] = {"main": [[{"node": "Save Output — Domain Synthesis", "type": "main", "index": 0}]]}
conns["Save Output — Domain Synthesis"] = {"main": [[{"node": "Update Sheets — Domain Synthesis", "type": "main", "index": 0}]]}
conns["Update Sheets — Domain Synthesis"] = {"main": [[{"node": "Parse Domain Synthesis", "type": "main", "index": 0}]]}

# Reconnect: Merge Interpretation Results now feeds ONLY the domain synthesis
# (previously it fanned out to old synthesis + 4 standalone branches).
conns["Merge Interpretation Results"] = {"main": [[{"node": "Build Domain Synthesis Payload", "type": "main", "index": 0}]]}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 4 — six "writer" branches (Claude, warm Russian register, per domain)
# ═══════════════════════════════════════════════════════════════════════════

WRITER_SYSTEM_PROMPT_TEMPLATE = r"""You are a writer with deep psychological insight and the
ability to make people feel genuinely seen — not analyzed, but recognized.

You are writing ONE domain of a six-part personal document. The other five domains exist as
separate files the client reads independently — do not summarize or reference their full
content, you only have your own domain's material below.

THE CORE PRINCIPLE — contact, not analysis:
Analysis says: "You tend to carry responsibility alone."
Contact says: "You learned very early that needing someone was dangerous. And you got so good
at not needing anyone that eventually you forgot you ever did."
Operate at the level of contact throughout.

WRITING RULES:
- Write in Russian throughout
- Address as {address_form}, gender: {gender}
- Zero esoteric terminology — find the human equivalent for every concept
- Never name the systems (BaZi, Jyotish, etc.) that produced the insights
- No generic sentences — if a sentence could appear in anyone else's document, rewrite it
- No practical exercises, no homework, no action steps
- {length_instruction}

OUTPUT: the document body only. No preamble, no meta-commentary, no markdown headers beyond
what's natural to the prose. Start directly with the text."""

DOMAIN_CONFIGS = [
    # (key, file_label, title_ru, length_instruction)
    ("frontend",  "Характер",            "Кто ты",
     "Length: 600-800 words. Open with the sharpest single truth from the material, "
     "expressed as an experience, not a trait."),
    ("backend",   "Внутреннее устройство", "Как ты устроен(а)",
     "Length: 700-900 words. Sit with bottlenecks before naming power sources — "
     "don't rush the hard parts into a silver lining."),
    ("timing",    "Тайминг и прогноз",    "Где ты сейчас",
     "Length: 600-800 words. Be honest about difficult windows; do not manufacture optimism."),
    ("relations", "Отношения",            "Ты в отношениях",
     "Length: 600-800 words. Name the attraction-vs-compatibility gap directly, "
     "without softening it into 'balance'."),
    ("career",    "Карьера и место",      "Призвание и место в мире",
     "Length: 600-800 words. Practical and specific — name qualities of environment "
     "and role, not job titles."),
    ("intimacy",  "Интимный профиль",     "Близость",
     "Length: 700-900 words. Never explicit. Somatic, psychological, archetypal register only."),
]

XW, YW, STEPW = 4840, 1900, 220
row_height = 220

for i, (key, file_label, title_ru, length_instr) in enumerate(DOMAIN_CONFIGS):
    y = YW + i * row_height
    cap_key = key.capitalize()

    is_intimacy = (key == "intimacy")

    writer_system_prompt = WRITER_SYSTEM_PROMPT_TEMPLATE.format(
        address_form="ADDR_PLACEHOLDER", gender="GENDER_PLACEHOLDER",
        length_instruction=length_instr,
    )
    # Substitute JS template-literal interpolations AFTER .format() runs,
    # so the single-brace ${...} syntax survives intact into the JS source
    # (running it through .format() directly would either collide with the
    # str.format() brace-escaping rules or, if escaped, double the braces
    # into invalid JS — confirmed bug, fixed here).
    writer_system_prompt = writer_system_prompt.replace(
        "ADDR_PLACEHOLDER", "${d.address_form}"
    ).replace(
        "GENDER_PLACEHOLDER", "${d.gender}"
    )

    build_js = f"""
const d = $input.first().json;
const domainText = d.synth_{key} || '';

if (!domainText) {{
  return [{{ json: {{ ...d, doc_{key}: 'Материал для этого домена недоступен — секция синтеза пуста.' }} }}];
}}

const systemPrompt = `{writer_system_prompt}`;

const userPrompt = `Тема документа: "{title_ru}"

МАТЕРИАЛ ДЛЯ ЭТОГО ДОМЕНА (уже структурирован, не дублируй другие домены, пиши только это):
${{domainText}}`;

const body = {{
  model: 'claude-sonnet-4-20250514', max_tokens: 2500,
  system: systemPrompt,
  messages: [{{ role: 'user', content: userPrompt }}]
}};

return [{{ json: {{ ...d, writer_{key}_payload: JSON.stringify(body) }} }}];
""".strip()

    save_js = f"""
const response = $input.first().json;
const doc_{key} = response.content?.[0]?.text || '';
const prev = $('Build {cap_key} Writer Payload').item.json;
return [{{ json: {{ ...prev, doc_{key} }} }}];
""".strip()

    build_id   = f"build-writer-{key}"
    http_id    = f"http-writer-{key}"
    save_id    = f"save-writer-{key}"
    sheets_id  = f"sheets-writer-{key}"
    prep_id    = f"prep-writer-{key}"
    send_id    = f"send-writer-{key}"

    build_name  = f"Build {cap_key} Writer Payload"
    http_name   = f"Dialog — {cap_key} Writer (Claude Sonnet)"
    save_name   = f"Save Output — {cap_key} Document"
    sheets_name = f"Update Sheets — {cap_key}"
    prep_name   = f"Prepare {cap_key} Document File"
    send_name   = f"Telegram — Send {cap_key} Document"

    nodes += [
        code_node(build_id, build_name, build_js, XW, y),
        claude_http(http_id, http_name, f"writer_{key}_payload", XW + STEPW, y),
        code_node(save_id, save_name, save_js, XW + 2 * STEPW, y),
        sheets_update(sheets_id, sheets_name, f"doc_{key}", XW + 3 * STEPW, y),
        code_node(prep_id, prep_name, prepare_file_js(f"doc_{key}", file_label), XW + 4 * STEPW, y),
        telegram_send_doc(send_id, send_name, XW + 5 * STEPW, y),
    ]

    conns[build_name]  = {"main": [[{"node": http_name, "type": "main", "index": 0}]]}
    conns[http_name]   = {"main": [[{"node": save_name, "type": "main", "index": 0}]]}
    conns[save_name]   = {"main": [[{"node": sheets_name, "type": "main", "index": 0}]]}
    conns[sheets_name] = {"main": [[{"node": prep_name, "type": "main", "index": 0}]]}
    conns[prep_name]   = {"main": [[{"node": send_name, "type": "main", "index": 0}]]}

    if not is_intimacy:
        # Unconditional: Parse Domain Synthesis fans out to this writer directly.
        conns.setdefault("Parse Domain Synthesis", {"main": [[]]})
        conns["Parse Domain Synthesis"]["main"][0].append(
            {"node": build_name, "type": "main", "index": 0}
        )

# ── Intimacy: gated by the existing intimacy_opt_in flag ────────────────────
# (the field was added to Parse Client Data in the previous iteration and
#  survives unchanged through the whole pipeline via {...d} spreads)

if_intimacy = if_node("if-intimacy-gate", "IF: Intimacy Opt-In?",
                      "={{ $json.intimacy_opt_in }}", XW - STEPW, YW + 5 * row_height)
nodes.append(if_intimacy)

conns["Parse Domain Synthesis"]["main"][0].append(
    {"node": "IF: Intimacy Opt-In?", "type": "main", "index": 0}
)
conns["IF: Intimacy Opt-In?"] = {"main": [
    [{"node": "Build Intimacy Writer Payload", "type": "main", "index": 0}],
    [],  # false branch: silent skip, no message
]}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 5 — Compass: ultra-short message, NOT a file
# ═══════════════════════════════════════════════════════════════════════════

XC, YC = 4840, YW + 6 * row_height

compass_build_js = r"""
const d = $input.first().json;
const compassText = d.synth_compass || '';

if (!compassText) {
  return [{ json: { ...d, compass_message: '⚠️ Компас недоступен — секция синтеза пуста.' } }];
}

const body = {
  model: 'claude-haiku-4-5-20251001', max_tokens: 600,
  messages: [{
    role: 'user',
    content: `Сожми этот материал в личный "техпаспорт" — телеграм-сообщение, не файл.
Формат — три блока, сухо и точно, без воды, без эзотерики:

КАК УСТРОЕН(А) (2-3 строки)
ЧТО ТОРМОЗИТ (2-3 строки)
ОТКУДА СИЛА (2-3 строки)

Обращение: ${d.address_form}. Имя: ${d.name}.
Максимум 180 слов суммарно. Это сообщение, к которому человек возвращается,
когда забыл, кто он — каждое слово должно быть необходимым.

МАТЕРИАЛ:
${compassText}`
  }]
};

return [{ json: { ...d, compass_payload: JSON.stringify(body) } }];
"""

compass_save_js = r"""
const response = $input.first().json;
const compass_message = response.content?.[0]?.text || '';
const prev = $('Build Compass Payload').item.json;
return [{ json: { ...prev, compass_message } }];
"""

nodes += [
    code_node("build-compass", "Build Compass Payload", compass_build_js, XC, YC),
    claude_http("http-compass", "Dialog — Compass (Claude Haiku)", "compass_payload", XC + STEP, YC, timeout=60000),
    code_node("save-compass", "Save Output — Compass", compass_save_js, XC + 2 * STEP, YC),
    telegram_send_text("send-compass", "Telegram — Send Compass Message",
                       "={{ $json.compass_message }}", XC + 3 * STEP, YC),
    sheets_update("sheets-final-status", "Update Status in Sheets", "compass_message", XC + 4 * STEP, YC),
]

conns["Parse Domain Synthesis"]["main"][0].append(
    {"node": "Build Compass Payload", "type": "main", "index": 0}
)
conns["Build Compass Payload"] = {"main": [[{"node": "Dialog — Compass (Claude Haiku)", "type": "main", "index": 0}]]}
conns["Dialog — Compass (Claude Haiku)"] = {"main": [[{"node": "Save Output — Compass", "type": "main", "index": 0}]]}
conns["Save Output — Compass"] = {"main": [[{"node": "Telegram — Send Compass Message", "type": "main", "index": 0}]]}
conns["Telegram — Send Compass Message"] = {"main": [[{"node": "Update Status in Sheets", "type": "main", "index": 0}]]}

# ═══════════════════════════════════════════════════════════════════════════
#  STEP 6 — validate & save
# ═══════════════════════════════════════════════════════════════════════════

node_names = {n['name'] for n in nodes}
errors = []
for src, targets in conns.items():
    if src not in node_names:
        errors.append(f"DANGLING SOURCE KEY: '{src}' has connections but no matching node")
    for branch in targets.get('main', []):
        for link in branch:
            if link.get('node') and link['node'] not in node_names:
                errors.append(f"BROKEN LINK: {src} → {link['node']}")

if errors:
    print("VALIDATION ERRORS:")
    for e in errors:
        print(" ", e)
    raise SystemExit(1)

json.dump(wf, open(DST, 'w'), ensure_ascii=False, indent=2)

print("v6 build complete — domain-partitioned synthesis + 6-file delivery + compass.")
print(f"Total nodes: {len(nodes)}")
print()
print("Removed:", 30, "old nodes (single-blob synthesis, single doc+passport, 4 standalone branches)")
print("Added:  ", "domain synthesis (5 nodes) + 6 writer chains (6x6 nodes) + compass (5 nodes) + 1 IF-gate")
print()
print("Delivery per run:")
print("  6 .txt files: Характер, Внутреннее устройство, Тайминг и прогноз,")
print("                Отношения, Карьера и место, [Интимный профиль — opt-in]")
print("  1 Telegram message: Компас (техпаспорт, ~180 слов)")

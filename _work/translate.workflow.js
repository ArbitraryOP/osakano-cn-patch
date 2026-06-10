export const meta = {
  name: 'translate-te',
  description: 'Fan out JP->ZH translation of .te scenario chunks (equal-length, glossary-consistent)',
  phases: [{ title: 'Translate', detail: 'one subagent per chunk' }],
}

const GLOSSARY = [
  '人名: 舞=舞, 葵=葵, 茜=茜, ヒロ=广, 純子=纯子, 弘子=弘子, 達也=达也, 龍童/鬼嶋龍童=龙童/鬼岛龙童,',
  '健二=健二, 的場=的场, 京一=京一, 耕二=耕二, 堀内=堀内, ミオ=美绪, ユイ=由衣, ゆかり=由香里, アヤ=阿雅, 舞の母=舞之母.',
  '地名: 通学路=上学路, ゴミ捨て場=垃圾场, リビング=客厅, 舞の部屋=舞的房间, 風呂場=浴室, 体育館=体育馆,',
  '大居埠頭=大居码头, プール=泳池, 校庭=校园, 廊下=走廊, 教室=教室. UI: セーブ=存档, ロード=读档, コンフィグ=设置.',
].join(' ')

let chunks = args || []
if (typeof chunks === 'string') chunks = JSON.parse(chunks)
if (!Array.isArray(chunks)) chunks = chunks.chunks || []
log(`translating ${chunks.length} chunks`)

const CHUNKDIR = 'E:\\game\\_work\\chunks\\'
const PARTDIR = 'E:\\game\\_work\\translated_parts\\'
function pathsFor(ch) {
  const base = `${ch.name}__${ch.start_id}_${ch.end_id}`
  return { in_path: CHUNKDIR + base + '.in.json', out_path: PARTDIR + base + '.json' }
}

const SCHEMA = {
  type: 'object',
  additionalProperties: false,
  properties: {
    ok: { type: 'boolean' },
    count: { type: 'number' },
    note: { type: 'string' },
  },
  required: ['ok', 'count'],
}

function prompt(ch) {
  const p = pathsFor(ch)
  return [
    `You are a professional Japanese->Simplified-Chinese game localizer for the 2005 visual novel "幼なじみな彼女" (a romance/adult VN). Translate faithfully and naturally.`,
    ``,
    `STEP 1: Read this UTF-8 JSON file: ${p.in_path}`,
    `It is an array of records {"id":int, "spans":[japanese strings...]}. Each span is one on-screen text fragment.`,
    ``,
    `STEP 2: Translate EVERY span to Simplified Chinese, then Write a new UTF-8 JSON file to EXACTLY this path: ${p.out_path}`,
    `Output = a JSON array of {"id": <same id>, "zh_spans": [<zh for span0>, <zh for span1>, ...]}.`,
    `Each record's zh_spans must have the SAME number of entries as its spans, same order.`,
    ``,
    `HARD RULES (a wrong length corrupts the game binary):`,
    `1) LENGTH CAP: for EACH span, the Chinese must use <= the SAME number of characters as the Japanese span. Count every full-width char, kana, or kanji as 1. Half-width ASCII counts as 0.5. SHORTER is fine (auto-padded); LONGER is forbidden -> condense wording, drop fillers, keep core meaning.`,
    `2) Punctuation stays FULL-WIDTH: 「」『』（）…！？、。—. Never introduce half-width ,.!? . Keep 「」 quotes as 「」.`,
    `3) GLOSSARY (use consistently): ${GLOSSARY}`,
    `4) TONE: natural spoken Chinese. Leads = warm childhood-romance; delinquents (鬼岛龙童 等) = crude street slang. Adult/explicit lines: translate plainly and faithfully (localizing existing fiction).`,
    `5) System/UI fragments translate tightly, e.g. ファイルが見つかりません=找不到文件, 未解放のリソースがあります=有未释放的资源, 全体=总计, 使用しない=不使用.`,
    `6) Keep pure symbols/digits unchanged. Never output romaji or Japanese kana in the result.`,
    ``,
    `STEP 3: After writing the file, report {ok:true, count:<number of records written>}. If the input was empty, write [] and report count:0.`,
    `Write ONLY that one output JSON file. Ensure it is valid JSON (double quotes, UTF-8).`,
  ].join('\n')
}

const results = await parallel(chunks.map((ch) => () =>
  agent(prompt(ch), {
    label: `tr:${ch.name}:${ch.start_id}-${ch.end_id}`,
    phase: 'Translate',
    schema: SCHEMA,
    agentType: 'general-purpose',
    model: 'sonnet',
  })
    .then((r) => ({ name: ch.name, start: ch.start_id, end: ch.end_id, ok: !!(r && r.ok), count: (r && r.count) || 0 }))
    .catch((e) => ({ name: ch.name, start: ch.start_id, end: ch.end_id, ok: false, err: String(e).slice(0, 160) }))
))

const okN = results.filter((r) => r && r.ok).length
log(`translate done: ${okN}/${chunks.length} ok`)
return { total: chunks.length, ok: okN, results }

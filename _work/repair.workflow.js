export const meta = {
  name: 'repair-te',
  description: 'Re-translate over-length records with a strict per-span char cap',
  phases: [{ title: 'Repair' }],
}

let chunks = args || []
if (typeof chunks === 'string') chunks = JSON.parse(chunks)
if (!Array.isArray(chunks)) chunks = chunks.chunks || []
log(`repairing ${chunks.length} files`)

const CHUNKDIR = 'E:\\game\\_work\\chunks\\'
const PARTDIR = 'E:\\game\\_work\\translated_parts\\'
function pathsFor(ch) {
  const inb = `${ch.name}__${ch.start_id}_${ch.end_id}`        // name = "repair_<tgt>"
  const outb = `${ch.tgt}__zzrepair_${ch.start_id}_${ch.end_id}` // round2, sorts after zrepair
  return { in_path: CHUNKDIR + inb + '.in.json', out_path: PARTDIR + outb + '.json' }
}

const GLOSSARY = '舞=舞,葵=葵,茜=茜,ヒロ=广,純子=纯子,弘子=弘子,達也=达也,龍童=龙童,健二=健二,ミオ=美绪,ユイ=由衣,アヤ=阿雅'

const SCHEMA = {
  type: 'object', additionalProperties: false,
  properties: { ok: { type: 'boolean' }, count: { type: 'number' } },
  required: ['ok', 'count'],
}

function prompt(ch) {
  const p = pathsFor(ch)
  return [
    `You are a JP->Simplified-Chinese game localizer doing a TIGHT re-translation pass.`,
    `Read: ${p.in_path} -- array of {"id":int, "spans":[{"jp":"...","max":N}]}.`,
    `For each span, translate jp to Simplified Chinese using AT MOST "max" Chinese characters — this is an ABSOLUTE hard cap (the byte budget is fixed). If max is small, abbreviate aggressively: use the shortest possible word, a single character, an interjection (啊/嗯/喂/哼), or onomatopoeia. NEVER exceed max even at the cost of nuance. Punctuation stays full-width 「」（）…！？、。.`,
    `Glossary: ${GLOSSARY}.`,
    `Write to EXACTLY: ${p.out_path} a JSON array of {"id":<same id>, "zh_spans":[<zh for span0>, ...]} (same order/count).`,
    `Then report {ok:true, count:<records>}.`,
  ].join('\n')
}

const results = await parallel(chunks.map((ch) => () =>
  agent(prompt(ch), { label: `rp:${ch.tgt}:${ch.start_id}-${ch.end_id}`, phase: 'Repair', schema: SCHEMA, agentType: 'general-purpose', model: 'sonnet' })
    .then((r) => ({ tgt: ch.tgt, ok: !!(r && r.ok), count: (r && r.count) || 0 }))
    .catch((e) => ({ tgt: ch.tgt, ok: false, err: String(e).slice(0, 160) }))
))
const okN = results.filter((r) => r && r.ok).length
log(`repair done: ${okN}/${chunks.length}`)
return { total: chunks.length, ok: okN, results }

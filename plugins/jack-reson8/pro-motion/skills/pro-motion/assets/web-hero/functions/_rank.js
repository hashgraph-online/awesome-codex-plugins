// 排位 = 报名顺序 − 每邀请 1 人往前 5 位
export const BOOST = 5;
const ALPHA = '0123456789ABCDEFGHJKMNPQRSTVWXYZ';

export function newRef() {
  const b = crypto.getRandomValues(new Uint8Array(6));
  return [...b].map(v => ALPHA[v % 32]).join('');
}

export async function rank(db, ref) {
  const row = await db.prepare(`
    WITH s AS (SELECT w.id, w.ref, w.id - ${BOOST} * (SELECT COUNT(*) FROM waitlist r WHERE r.referred_by = w.ref) AS score FROM waitlist w)
    SELECT me.ref AS ref,
           (SELECT COUNT(*) FROM s WHERE s.score < me.score OR (s.score = me.score AND s.id < me.id)) + 1 AS position,
           (SELECT COUNT(*) FROM waitlist r WHERE r.referred_by = me.ref) AS invites
    FROM s me WHERE me.ref = ?1`).bind(ref).first();
  return row ? { ref: row.ref, position: row.position, invites: row.invites, boost: BOOST } : null;
}

export const json = (body, status = 200) => new Response(JSON.stringify(body), {
  status, headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
});

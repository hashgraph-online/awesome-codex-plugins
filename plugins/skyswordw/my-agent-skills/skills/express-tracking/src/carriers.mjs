const ALIAS_MAP = new Map([
  ["jd", "jd"],
  ["jingdong", "jd"],
  ["京东", "jd"],
  ["京东快递", "jd"],
  ["sf", "shunfeng"],
  ["shunfeng", "shunfeng"],
  ["顺丰", "shunfeng"],
  ["顺丰速运", "shunfeng"],
  ["ems", "ems"],
  ["邮政", "ems"],
  ["中国邮政", "ems"],
  ["zto", "zhongtong"],
  ["zhongtong", "zhongtong"],
  ["中通", "zhongtong"],
  ["yto", "yuantong"],
  ["yuantong", "yuantong"],
  ["圆通", "yuantong"],
  ["sto", "shentong"],
  ["shentong", "shentong"],
  ["申通", "shentong"],
  ["deppon", "deppon"],
  ["德邦", "deppon"],
  ["best", "huitongkuaidi"],
  ["百世", "huitongkuaidi"]
]);

export function normalizeCarrier(rawCarrier) {
  const normalized = String(rawCarrier ?? "").trim().toLowerCase();
  if (!normalized) {
    return null;
  }
  return ALIAS_MAP.get(normalized) ?? normalized;
}

export function guessCarrierFromNumber(number) {
  const normalized = String(number ?? "").trim().toUpperCase();
  if (!normalized) {
    return null;
  }
  if (/^JD[A-Z0-9]+$/u.test(normalized)) {
    return "jd";
  }
  if (/^SF[A-Z0-9]+$/u.test(normalized)) {
    return "shunfeng";
  }
  if (/^YT[0-9A-Z]+$/u.test(normalized)) {
    return "yuantong";
  }
  if (/^ZT[0-9A-Z]+$/u.test(normalized)) {
    return "zhongtong";
  }
  return null;
}

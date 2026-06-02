import crypto from "node:crypto";

import { guessCarrierFromNumber, normalizeCarrier } from "./carriers.mjs";

const STATE_LABELS = new Map([
  ["0", "在途"],
  ["1", "揽收"],
  ["2", "疑难"],
  ["3", "签收"],
  ["4", "退签"],
  ["5", "派件"],
  ["6", "退回"],
  ["7", "转投"],
  ["8", "清关"],
  ["10", "待清关"],
  ["11", "清关中"],
  ["12", "已清关"],
  ["13", "清关异常"],
  ["14", "拒签"]
]);

export async function trackShipment(
  { number, carrier = null, phone = "", from = "", to = "" },
  { config, fetchImpl = globalThis.fetch }
) {
  if (!number) {
    throw new Error("缺少快递单号，请传入 --number。");
  }
  validateCredentials(config.kuaidi100);

  const carrierResolution = await resolveCarrier(number, carrier, config, fetchImpl);
  const payload = {
    num: number,
    com: carrierResolution.carrier,
    phone,
    from,
    to,
    resultv2: "1",
    show: "0",
    order: "desc"
  };
  const raw = await requestTracking(payload, config.kuaidi100, fetchImpl);
  const events = Array.isArray(raw.data) ? raw.data : [];
  const latest = events[0] ?? null;
  const stateCode = String(raw.state ?? "");

  return {
    number,
    carrier: carrierResolution.carrier,
    carrierSource: carrierResolution.source,
    stateCode,
    stateLabel: STATE_LABELS.get(stateCode) ?? String(latest?.status ?? raw.state ?? "未知"),
    statusCode: String(raw.status ?? ""),
    statusText: String(raw.message ?? "").trim(),
    latest,
    events,
    raw
  };
}

function validateCredentials(config) {
  if (!config.key) {
    throw new Error("缺少 EXPRESS_TRACKING_KUAIDI100_KEY。");
  }
  if (!config.customer) {
    throw new Error("缺少 EXPRESS_TRACKING_KUAIDI100_CUSTOMER。");
  }
}

async function resolveCarrier(number, carrier, config, fetchImpl) {
  const explicit = normalizeCarrier(carrier);
  if (explicit) {
    return { carrier: explicit, source: "user" };
  }

  const auto = await tryAutoCarrier(number, config.kuaidi100, fetchImpl);
  if (auto) {
    return { carrier: auto, source: "auto" };
  }

  const heuristic = guessCarrierFromNumber(number);
  if (heuristic) {
    return { carrier: heuristic, source: "heuristic" };
  }

  throw new Error(
    "无法自动识别快递公司。请补充 --carrier=<快递100公司编码>，例如 jd、shunfeng、ems。"
  );
}

async function tryAutoCarrier(number, config, fetchImpl) {
  const url = new URL(config.autoUrl);
  url.searchParams.set("num", number);
  url.searchParams.set("key", config.key);

  const response = await fetchImpl(url, {
    headers: {
      Accept: "application/json"
    }
  });

  if (!response.ok) {
    return null;
  }

  let payload;
  try {
    payload = await response.json();
  } catch {
    return null;
  }

  const candidates = Array.isArray(payload?.data) ? payload.data : Array.isArray(payload?.auto) ? payload.auto : [];
  for (const candidate of candidates) {
    const normalized = normalizeCarrier(candidate?.comCode ?? candidate?.comcode ?? candidate?.number ?? "");
    if (normalized) {
      return normalized;
    }
  }
  return null;
}

async function requestTracking(paramObject, config, fetchImpl) {
  const param = JSON.stringify(paramObject);
  const sign = crypto
    .createHash("md5")
    .update(`${param}${config.key}${config.customer}`, "utf8")
    .digest("hex")
    .toUpperCase();

  const body = new URLSearchParams({
    customer: config.customer,
    sign,
    param
  });

  const response = await fetchImpl(config.queryUrl, {
    method: "POST",
    headers: {
      Accept: "application/json",
      "Content-Type": "application/x-www-form-urlencoded"
    },
    body
  });

  if (!response.ok) {
    throw new Error(`快递100请求失败：HTTP ${response.status}`);
  }

  const payload = await response.json();
  const statusCode = String(payload?.status ?? payload?.returnCode ?? "");
  const success = statusCode === "200" || payload?.result === true;

  if (!success) {
    const message = String(payload?.message ?? payload?.reason ?? "快递100返回失败");
    throw new Error(message);
  }

  return payload;
}

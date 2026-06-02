export function formatTrackingSummary(result, { recentLimit = 3 } = {}) {
  const lines = [];
  lines.push(`快递单号：${result.number}`);
  lines.push(`快递公司：${result.carrier}${formatCarrierSource(result.carrierSource)}`);
  lines.push(`物流状态：${result.stateLabel}`);

  if (result.latest?.time) {
    lines.push(`最新时间：${result.latest.time}`);
  }
  if (result.latest?.context) {
    lines.push(`最新轨迹：${result.latest.context}`);
  }

  const events = Array.isArray(result.events) ? result.events.slice(0, recentLimit) : [];
  if (events.length > 0) {
    lines.push("最近轨迹：");
    for (const event of events) {
      const time = event.time ?? event.ftime ?? "未知时间";
      const context = event.context ?? "";
      lines.push(`- ${time} ${context}`.trim());
    }
  }

  return lines.join("\n");
}

export function formatTrackingJson(result, { recentLimit = 3 } = {}) {
  return {
    provider: "kuaidi100",
    number: result.number,
    carrier: {
      code: result.carrier,
      source: result.carrierSource
    },
    state: {
      code: result.stateCode,
      label: result.stateLabel
    },
    status: {
      code: result.statusCode,
      message: result.statusText
    },
    latestEvent: normalizeEvent(result.latest),
    recentEvents: normalizeEvents(result.events, recentLimit)
  };
}

function formatCarrierSource(source) {
  switch (source) {
    case "user":
      return "（手动指定）";
    case "auto":
      return "（自动识别）";
    case "heuristic":
      return "（前缀推断）";
    default:
      return "";
  }
}

function normalizeEvents(events, recentLimit) {
  if (!Array.isArray(events)) {
    return [];
  }
  return events.slice(0, recentLimit).map(normalizeEvent).filter(Boolean);
}

function normalizeEvent(event) {
  if (!event) {
    return null;
  }
  return {
    time: event.time ?? event.ftime ?? "",
    context: event.context ?? ""
  };
}

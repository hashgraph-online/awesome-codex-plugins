import { loadConfig } from "./config.mjs";
import { formatTrackingJson, formatTrackingSummary } from "./format.mjs";
import { trackShipment } from "./kuaidi100.mjs";

export async function runCli({ argv = process.argv.slice(2), cwd = process.cwd(), env = process.env, fetchImpl = globalThis.fetch } = {}) {
  const config = loadConfig({ argv, cwd, env });
  if (!config.number) {
    throw new Error("缺少 --number=<tracking-number>。");
  }

  const result = await trackShipment(
    {
      number: config.number,
      carrier: config.carrier,
      phone: config.phone,
      from: config.from,
      to: config.to
    },
    { config, fetchImpl }
  );

  if (config.json) {
    const payload = formatTrackingJson(result, { recentLimit: config.recentLimit });
    console.log(JSON.stringify(payload, null, 2));
    return payload;
  }

  console.log(formatTrackingSummary(result, { recentLimit: config.recentLimit }));
  return result;
}

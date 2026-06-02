#!/usr/bin/env node

async function loadRuntime() {
  try {
    return await import("../src/run-captcha.mjs");
  } catch (error) {
    if (error?.code === "ERR_MODULE_NOT_FOUND") {
      console.error(
        "Missing skill runtime dependencies. Run `npm install` in this skill directory before the first use."
      );
      process.exit(1);
    }
    throw error;
  }
}

async function main() {
  const { runCaptchaFromConfig } = await loadRuntime();
  const result = await runCaptchaFromConfig();

  if (process.argv.includes("--json")) {
    console.log(JSON.stringify(result, null, 2));
    return;
  }

  if (result.success) {
    console.log(`captcha=${result.text}`);
    console.log(`provider=${result.resolvedProvider ?? "local_ocr"}`);
    console.log(`model=${result.resolvedModel ?? "n/a"}`);
  } else {
    console.log("captcha recognition failed");
    console.log(JSON.stringify(result, null, 2));
    process.exitCode = 1;
  }
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});

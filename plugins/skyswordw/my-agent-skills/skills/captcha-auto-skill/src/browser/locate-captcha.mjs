export async function locateCaptchaTargets(page) {
  const captchaLocator = await firstVisible(page, [
    'img[id*="captcha" i]',
    'img[src*="captcha" i]',
    'img[alt*="captcha" i]',
    'canvas[id*="captcha" i]'
  ]);

  if (!captchaLocator) {
    throw new Error("Unable to locate captcha element on the page.");
  }

  const inputLocator = await firstVisible(page, [
    'input[id*="captcha" i]',
    'input[name*="captcha" i]',
    'input[placeholder*="验证码"]',
    'input[placeholder*="captcha" i]'
  ]);
  const submitLocator = await firstVisible(page, [
    'button[type="submit"]',
    'input[type="submit"]',
    'button:has-text("Submit")',
    'button:has-text("验证")',
    'button:has-text("登录")'
  ]);

  return {
    captchaBuffer: await captchaLocator.screenshot({ type: "png" }),
    fill: inputLocator ? async (text) => inputLocator.fill(text) : null,
    submit: submitLocator ? async () => submitLocator.click() : null
  };
}

async function firstVisible(page, selectors) {
  for (const selector of selectors) {
    const locator = page.locator(selector).first();
    if (await locator.count()) {
      try {
        if (await locator.isVisible()) {
          return locator;
        }
      } catch {
        continue;
      }
    }
  }
  return null;
}

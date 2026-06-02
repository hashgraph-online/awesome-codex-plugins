export function interpretCaptchaText(rawText) {
  const normalizedInput = String(rawText)
    .toUpperCase()
    .replace(/\s+/g, "")
    .replace(/×/gu, "X");

  const arithmetic = parseArithmeticCaptcha(normalizedInput);
  if (arithmetic) {
    return {
      text: String(arithmetic),
      kind: "arithmetic",
      normalizedInput
    };
  }

  return {
    text: normalizedInput.replace(/[^A-Z0-9]/g, ""),
    kind: "text",
    normalizedInput: normalizedInput.replace(/[^A-Z0-9]/g, "")
  };
}

function parseArithmeticCaptcha(normalizedInput) {
  const match = normalizedInput.match(/^(\d+)([+\-X*/])(\d+)(?:[=?])?$/u);
  if (!match) {
    return null;
  }

  const left = Number.parseInt(match[1], 10);
  const operator = match[2];
  const right = Number.parseInt(match[3], 10);

  switch (operator) {
    case "+":
      return left + right;
    case "-":
      return left - right;
    case "X":
    case "*":
      return left * right;
    case "/":
      if (right === 0 || left % right !== 0) {
        return null;
      }
      return left / right;
    default:
      return null;
  }
}

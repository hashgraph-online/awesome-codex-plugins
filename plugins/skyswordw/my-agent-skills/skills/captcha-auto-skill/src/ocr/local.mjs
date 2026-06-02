import { createWorker } from "tesseract.js";

import { interpretCaptchaText } from "../captcha/text.mjs";
import { preprocessCaptchaImage } from "./preprocess.mjs";

export const OCR_CONFIDENCE_THRESHOLD = 60;
export const CAPTCHA_MIN_LENGTH = 1;
export const CAPTCHA_MAX_LENGTH = 12;

export async function runLocalOcr({
  inputPath,
  workerFactory = defaultWorkerFactory
}) {
  const preprocessed = await preprocessCaptchaImage({ inputPath });
  const worker = await workerFactory();

  try {
    const result = await worker.recognize(preprocessed.buffer);
    const confidence = Number(result?.data?.confidence ?? 0);
    const interpreted = interpretCaptchaText(result?.data?.text ?? "");
    const text = interpreted.text;

    if (!text) {
      return buildFailure("empty_text", confidence);
    }
    if (confidence < OCR_CONFIDENCE_THRESHOLD) {
      return buildFailure("low_confidence", confidence);
    }
    if (text.length < CAPTCHA_MIN_LENGTH || text.length > CAPTCHA_MAX_LENGTH) {
      return buildFailure("invalid_length", confidence);
    }

    return {
      success: true,
      text,
      confidence,
      method: "local_ocr",
      shouldShortCircuit: true
    };
  } finally {
    if (typeof worker.terminate === "function") {
      await worker.terminate();
    }
  }
}

async function defaultWorkerFactory() {
  return createWorker("eng", 1);
}

function buildFailure(reason, confidence) {
  return {
    success: false,
    text: null,
    confidence,
    method: "local_ocr",
    shouldShortCircuit: false,
    reason
  };
}

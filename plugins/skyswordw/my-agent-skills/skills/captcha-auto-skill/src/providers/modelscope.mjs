import { DEFAULT_MODELSCOPE_BASE_URL } from "../config.mjs";
import { isDeniedModel } from "../model-preferences.mjs";
import { interpretCaptchaText } from "../captcha/text.mjs";

export async function runModelScopeVisionInference({
  apiKey,
  model,
  imageBuffer,
  baseUrl = DEFAULT_MODELSCOPE_BASE_URL,
  fetchImpl = fetch,
  logger = () => {}
}) {
  if (isDeniedModel(model)) {
    return buildFailure({
      provider: "modelscope",
      model,
      retryable: false,
      reason: "denylisted_model"
    });
  }

  if (!hasApiKey(apiKey)) {
    return buildFailure({
      provider: "modelscope",
      model,
      retryable: false,
      reason: "missing_api_key",
      message:
        "Missing CAPTCHA_MODELSCOPE_API_KEY. Set it in the current shell or the project-local .env.local."
    });
  }

  return runVisionInference({
    provider: "modelscope",
    apiKey,
    model,
    imageBuffer,
    baseUrl,
    fetchImpl,
    logger
  });
}

async function runVisionInference({
  provider,
  apiKey,
  model,
  imageBuffer,
  baseUrl,
  fetchImpl,
  logger
}) {
  try {
    const response = await fetchImpl(`${baseUrl}/chat/completions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${apiKey}`
      },
      body: JSON.stringify({
        model,
        messages: [
          {
            role: "user",
            content: [
              {
                type: "text",
                text: "Read the captcha image. Return only the captcha characters. If unreadable, return UNRECOGNIZABLE."
              },
              {
                type: "image_url",
                image_url: {
                  url: `data:image/png;base64,${Buffer.from(imageBuffer).toString("base64")}`
                }
              }
            ]
          }
        ],
        max_tokens: 32,
        temperature: 0.1
      })
    });

    if (!response.ok) {
      logger(`${provider} request failed with status ${response.status}`);
      return buildFailure({
        provider,
        model,
        retryable: true,
        reason: "transport_error"
      });
    }

    const payload = await response.json();
    const content = payload?.choices?.[0]?.message?.content;
    if (!content) {
      return buildFailure({
        provider,
        model,
        retryable: true,
        reason: "empty_choice"
      });
    }

    const text = interpretCaptchaText(content).text;
    if (!text || text === "UNRECOGNIZABLE") {
      return buildFailure({
        provider,
        model,
        retryable: true,
        reason: "empty_choice"
      });
    }

    return {
      success: true,
      text,
      resolvedProvider: provider,
      resolvedModel: model,
      rawResponseMeta: {
        choiceCount: payload.choices.length
      }
    };
  } catch (error) {
    logger(`${provider} request failed: ${error.message}`);
    return buildFailure({
      provider,
      model,
      retryable: true,
      reason: "transport_error"
    });
  }
}

function buildFailure({ provider, model, retryable, reason, message = null }) {
  return {
    success: false,
    text: null,
    resolvedProvider: provider,
    resolvedModel: model,
    retryable,
    reason,
    message
  };
}

function hasApiKey(apiKey) {
  return typeof apiKey === "string" && apiKey.trim().length > 0;
}

import { DEFAULT_DASHSCOPE_BASE_URL } from "../config.mjs";
import { interpretCaptchaText } from "../captcha/text.mjs";

export async function runDashScopeVisionInference({
  apiKey,
  model,
  imageBuffer,
  baseUrl = DEFAULT_DASHSCOPE_BASE_URL,
  fetchImpl = fetch,
  logger = () => {}
}) {
  if (!hasApiKey(apiKey)) {
    return buildFailure({
      model,
      retryable: false,
      reason: "missing_api_key",
      message:
        "Missing CAPTCHA_DASHSCOPE_API_KEY. Set it in the current shell or the project-local .env.local."
    });
  }

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
      logger(`dashscope request failed with status ${response.status}`);
      return buildFailure(model, true, "transport_error");
    }

    const payload = await response.json();
    const content = payload?.choices?.[0]?.message?.content;
    if (!content) {
      return buildFailure(model, true, "empty_choice");
    }

    const text = interpretCaptchaText(content).text;
    if (!text || text === "UNRECOGNIZABLE") {
      return buildFailure(model, true, "empty_choice");
    }

    return {
      success: true,
      text,
      resolvedProvider: "dashscope",
      resolvedModel: model,
      rawResponseMeta: {
        choiceCount: payload.choices.length
      }
    };
  } catch (error) {
    logger(`dashscope request failed: ${error.message}`);
    return buildFailure(model, true, "transport_error");
  }
}

function buildFailure(input, retryable, reason) {
  const payload =
    typeof input === "object" && input !== null
      ? input
      : {
          model: input,
          retryable,
          reason
        };

  return {
    success: false,
    text: null,
    resolvedProvider: "dashscope",
    resolvedModel: payload.model,
    retryable: payload.retryable,
    reason: payload.reason,
    message: payload.message ?? null
  };
}

function hasApiKey(apiKey) {
  return typeof apiKey === "string" && apiKey.trim().length > 0;
}

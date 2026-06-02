export const MODELSCOPE_DENYLIST = [
  "Qwen/Qwen3-VL-8B-Instruct",
  "Qwen/Qwen3-VL-235B-A22B-Instruct"
];

export const MODELSCOPE_PREFERRED_MODELS = [
  "Qwen/Qwen3.5-397B-A17B",
  "OpenGVLab/InternVL3_5-241B-A28B",
  "PaddlePaddle/ERNIE-4.5-VL-28B-A3B-PT"
];

export const DASHSCOPE_DEFAULT_MODEL = "qwen3.6-plus";
export const DASHSCOPE_PINNED_FALLBACK_MODEL = "qwen3.6-plus-2026-04-02";

export function isDeniedModel(modelId) {
  return MODELSCOPE_DENYLIST.includes(modelId);
}

/*
 * paper-preset.js: load a Paper Shaders preset into a ShaderMount and draw it
 * one frame at a time from a video timeline (HyperFrames or Remotion).
 *
 * Part of the varg `paper-shaders` skill (MIT). Paper Shaders itself is
 * Apache-2.0; see LICENSE-paper-shaders and NOTICE next to SKILL.md.
 *
 * This file imports nothing. Pass the @paper-design/shaders module namespace as
 * `PS`, so the same file works with a CDN import, node_modules or a vendored copy.
 */

/** The Paper Shaders release the presets were checked against. Pin this exact version. */
export const PAPER_SHADERS_VERSION = "0.0.82";

// Props whose string value indexes an exported enum, per shader.
const ENUMS = {
  Dithering: { shape: "DitheringShapes", type: "DitheringTypes" },
  DotGrid: { shape: "DotGridShapes" },
  FlutedGlass: { distortionShape: "GlassDistortionShapes", shape: "GlassGridShapes" },
  GemSmoke: { shape: "GemSmokeShapes" },
  GrainGradient: { shape: "GrainGradientShapes" },
  HalftoneCmyk: { type: "HalftoneCmykTypes" },
  HalftoneDots: { grid: "HalftoneDotsGrids", type: "HalftoneDotsTypes" },
  ImageDithering: { type: "DitheringTypes" },
  LiquidMetal: { shape: "LiquidMetalShapes" },
  PulsingBorder: { aspectRatio: "PulsingBorderAspectRatios" },
  Warp: { shape: "WarpPatterns" },
};

// Props whose uniform is not named `u_<prop>`.
const RENAMES = {
  Dithering: { size: "u_pxSize" },
  DotGrid: { size: "u_dotSize" },
  ImageDithering: { size: "u_pxSize" },
};

// Image shaders that turn the image into a mask before sampling it.
const PREPROCESS = {
  GemSmoke: "toProcessedGemSmoke",
  Heatmap: "toProcessedHeatmap",
  LiquidMetal: "toProcessedLiquidMetal",
};

// Image shaders that sample u_image with mipmaps.
const MIPMAPS = ["FlutedGlass", "GemSmoke", "Heatmap", "LensDistortion", "LiquidMetal", "PaperTexture", "Water"];

// Sizing uniforms the shared vertex shader reads for every shader.
const SIZING = ["u_fit", "u_scale", "u_rotation", "u_originX", "u_originY", "u_offsetX", "u_offsetY", "u_worldWidth", "u_worldHeight"];

// Uniforms ShaderMount sets itself.
const ENGINE = new Set(["u_time", "u_resolution", "u_pixelRatio", "u_imageAspectRatio"]);

/**
 * Shader time in milliseconds for a timeline position in seconds:
 * `motion.frame + seconds * 1000 * motion.timeScale`. `timeScale` is the number
 * shaders.paper.design calls `speed`; the mount itself always runs at speed 0.
 */
export function shaderFrame(preset, seconds, options = {}) {
  const timeScale = options.timeScale ?? preset.motion?.timeScale ?? 1;
  const frame = options.frame ?? preset.motion?.frame ?? 0;
  return frame + seconds * 1000 * timeScale;
}

/**
 * Uniforms for plain params (numbers, booleans, colors, enums); images are not
 * allowed here. Use it to change params over time with ShaderMount.setUniforms.
 */
export function paramsToUniforms(PS, shader, params) {
  const uniforms = {};
  for (const [key, value] of Object.entries(params)) {
    if (key === "speed" || key === "frame") continue;
    if (key === "image") throw new Error("paper-shaders: images are set once, at mount time");
    if (key === "colors") {
      uniforms.u_colors = value.map(PS.getShaderColorFromString);
      uniforms.u_colorsCount = value.length;
    } else if (key === "fit") {
      uniforms.u_fit = lookup(PS, "ShaderFitOptions", value);
    } else if (ENUMS[shader]?.[key]) {
      uniforms[`u_${key}`] = lookup(PS, ENUMS[shader][key], value);
    } else {
      uniforms[RENAMES[shader]?.[key] ?? `u_${key}`] = typeof value === "string" && /^color[A-Z]/.test(key) ? PS.getShaderColorFromString(value) : value;
    }
  }
  return uniforms;
}

/**
 * ShaderMount arguments for a preset. Every image is loaded first, because
 * ShaderMount throws on an image that has not finished loading. Throws if the
 * preset leaves a uniform without a value, instead of rendering a wrong frame.
 * `options.image` (a URL) overrides the preset's image, e.g. a logo or a still.
 */
export async function presetToMount(PS, preset, options = {}) {
  const name = preset.shader;
  const fragmentShader = PS[`${name[0].toLowerCase()}${name.slice(1)}FragmentShader`];
  if (typeof fragmentShader !== "string") throw new Error(`paper-shaders: unknown shader "${name}"`);

  const { image: presetImage, ...params } = preset.params;
  const image = options.image ?? presetImage ?? "";
  const uniforms = paramsToUniforms(PS, name, params);

  const declared = [...fragmentShader.matchAll(/uniform\s+[^;]*?\b(u_\w+)/g)].map((m) => m[1]);
  if (declared.includes("u_image")) uniforms.u_image = await loadImage(PS, name, image);
  if (declared.includes("u_isImage")) uniforms.u_isImage = Boolean(image);
  if (declared.includes("u_noiseTexture")) uniforms.u_noiseTexture = await decoded(PS.getShaderNoiseTexture());

  const missing = [...new Set([...declared, ...SIZING])].filter((u) => !(u in uniforms) && !ENGINE.has(u));
  if (missing.length) throw new Error(`paper-shaders: preset "${preset.id}" has no value for ${missing.join(", ")}`);

  return { fragmentShader, uniforms, mipmaps: MIPMAPS.includes(name) ? ["u_image"] : [] };
}

/**
 * Mount a preset into `element` (the canvas fills it) at speed 0, and resolve
 * once the canvas has its real size, so the first frame is drawn at full resolution.
 * `minPixelRatio` comes from options, then `preset.mount`, then Paper's default of 2.
 */
export async function mountPreset(PS, element, preset, options = {}) {
  const { fragmentShader, uniforms, mipmaps } = await presetToMount(PS, preset, options);
  const mount = new PS.ShaderMount(
    element,
    fragmentShader,
    uniforms,
    { preserveDrawingBuffer: true, ...options.contextAttributes },
    0,
    shaderFrame(preset, options.seconds ?? 0, options),
    options.minPixelRatio ?? preset.mount?.minPixelRatio ?? 2,
    options.maxPixelCount ?? preset.mount?.maxPixelCount,
    mipmaps,
  );
  await sized(mount.canvasElement);
  return mount;
}

/**
 * A HyperFrames frame source; pass it to `window.__hyperframes.registerFrameSource`.
 * `element` is the timed host: class="clip" with data-composition-id, data-start,
 * data-duration, data-track-index and data-no-timeline. HyperFrames calls `render`
 * with seconds since the host's start, in any order; each call draws synchronously.
 * `options.paramsAt(seconds)` may return params to change over time (a pure
 * function of `seconds`, e.g. a ray intensity ramp for a logo reveal).
 */
export function paperFrameSource(PS, element, preset, options = {}) {
  let mount = null;
  return {
    element,
    ready: mountPreset(PS, element, preset, options).then((m) => {
      mount = m;
    }),
    render: (seconds) => {
      if (options.paramsAt) mount.setUniforms(paramsToUniforms(PS, preset.shader, options.paramsAt(seconds)));
      mount.setFrame(shaderFrame(preset, seconds, options));
    },
    dispose: () => {
      mount?.dispose();
      mount = null;
    },
  };
}

/**
 * One host showing several presets in a row: preset i covers seconds [i × each, (i + 1) × each).
 * It holds a single WebGL context, so a film can show any number of looks without
 * hitting Chrome's limit of about 16 contexts per page. `presets` may be a promise.
 * `imageFor(preset)` returns an image URL or undefined; `onPreset(preset, index, local)`
 * runs on every frame, e.g. to update a caption.
 */
export function paperSequenceSource(PS, element, presets, { each, imageFor, onPreset, ...options }) {
  let list = [];
  let current = { index: -1, mount: null };
  return {
    element,
    ready: Promise.resolve(presets).then((loaded) => {
      list = loaded;
    }),
    render: async (seconds) => {
      const index = Math.min(Math.floor(seconds / each), list.length - 1);
      const preset = list[index];
      const local = seconds - index * each;
      if (current.index !== index) {
        current.mount?.dispose();
        current = { index, mount: null };
        current.mount = await mountPreset(PS, element, preset, { ...options, image: imageFor?.(preset) });
      }
      onPreset?.(preset, index, local);
      current.mount.setFrame(shaderFrame(preset, local, options));
    },
    dispose: () => {
      current.mount?.dispose();
      current = { index: -1, mount: null };
    },
  };
}

function lookup(PS, enumName, value) {
  const table = PS[enumName];
  if (!table || !(value in table)) throw new Error(`paper-shaders: "${value}" is not one of ${enumName}: ${Object.keys(table ?? {}).join(", ")}`);
  return table[value];
}

async function loadImage(PS, shader, src) {
  let url = src || PS.emptyPixel;
  if (src && PREPROCESS[shader]) {
    // LiquidMetal and GemSmoke return { pngBlob }, Heatmap returns { blob }.
    const processed = await PS[PREPROCESS[shader]](src);
    url = URL.createObjectURL(processed.pngBlob ?? processed.blob);
  }
  const img = new Image();
  if (/^https?:/.test(url) && new URL(url).origin !== location.origin) img.crossOrigin = "anonymous";
  img.src = url;
  return decoded(img);
}

// Same rule as the Paper Shaders React package: rasterize small and vector images at 1024 px or more.
async function decoded(img) {
  await img.decode();
  if (img.naturalWidth >= 1 && img.naturalHeight >= 1 && img.naturalWidth < 1024 && img.naturalHeight < 1024) {
    const aspect = img.naturalWidth / img.naturalHeight;
    img.width = Math.round(aspect > 1 ? 1024 * aspect : 1024);
    img.height = Math.round(aspect > 1 ? 1024 : 1024 / aspect);
  }
  return img;
}

// ShaderMount sizes its canvas from a ResizeObserver. An observer created after the
// mount's own is notified after it in the same delivery, so this resolves once the
// canvas has its final size.
function sized(canvas) {
  return new Promise((resolve) => {
    const observer = new ResizeObserver(() => {
      observer.disconnect();
      resolve();
    });
    observer.observe(canvas);
  });
}

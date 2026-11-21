// Types for paper-preset.js. `PS` is the @paper-design/shaders module namespace.
import type * as PaperShaders from "@paper-design/shaders";

type PS = typeof PaperShaders;

export interface PaperPreset {
  id: string;
  label?: string;
  shader: string;
  page?: string;
  paperShaders?: string;
  use?: string;
  image?: { role: string; required: boolean; note?: string };
  motion?: { timeScale?: number; frame?: number };
  mount?: { minPixelRatio?: number; maxPixelCount?: number };
  roles?: Record<string, string | string[]>;
  /** "paper" for Paper's built-in presets in presets/paper/. */
  origin?: string;
  params: Record<string, unknown>;
}

export interface MountOptions {
  /** Image URL for image presets (logo, still); overrides params.image. */
  image?: string;
  /** Timeline position the mount starts at, in seconds. */
  seconds?: number;
  timeScale?: number;
  frame?: number;
  minPixelRatio?: number;
  maxPixelCount?: number;
  contextAttributes?: WebGLContextAttributes;
}

export interface FrameSourceOptions extends MountOptions {
  paramsAt?: (seconds: number) => Record<string, unknown>;
}

export const PAPER_SHADERS_VERSION: string;
export function shaderFrame(preset: PaperPreset, seconds: number, options?: { timeScale?: number; frame?: number }): number;
export function paramsToUniforms(PS: PS, shader: string, params: Record<string, unknown>): PaperShaders.ShaderMountUniforms;
export function presetToMount(
  PS: PS,
  preset: PaperPreset,
  options?: { image?: string },
): Promise<{ fragmentShader: string; uniforms: PaperShaders.ShaderMountUniforms; mipmaps: string[] }>;
export function mountPreset(PS: PS, element: HTMLElement, preset: PaperPreset, options?: MountOptions): Promise<PaperShaders.ShaderMount>;
export function paperFrameSource(
  PS: PS,
  element: HTMLElement,
  preset: PaperPreset,
  options?: FrameSourceOptions,
): {
  element: HTMLElement;
  ready: Promise<void>;
  render: (seconds: number) => void;
  dispose: () => void;
};
export function paperSequenceSource(
  PS: PS,
  element: HTMLElement,
  presets: PaperPreset[] | Promise<PaperPreset[]>,
  options: MountOptions & {
    each: number;
    imageFor?: (preset: PaperPreset) => string | undefined;
    onPreset?: (preset: PaperPreset, index: number, localSeconds: number) => void;
  },
): {
  element: HTMLElement;
  ready: Promise<void>;
  render: (seconds: number) => Promise<void>;
  dispose: () => void;
};

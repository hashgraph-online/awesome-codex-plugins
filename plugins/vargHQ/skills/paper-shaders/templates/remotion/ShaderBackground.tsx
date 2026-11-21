/*
 * ShaderBackground: a Paper Shaders preset as a Remotion layer, drawn for the
 * current frame. Part of the varg `paper-shaders` skill (MIT); Paper Shaders is Apache-2.0.
 *
 *   npm i @paper-design/shaders@0.0.82        (exact version)
 *   copy templates/paper-preset.js, templates/paper-preset.d.ts and the preset JSON next to this file
 *   npx remotion render <composition-id> out.mp4 --gl=angle
 *
 *   <ShaderBackground preset={brandMesh}>
 *     <h1>Headline</h1>
 *   </ShaderBackground>
 */
import { useLayoutEffect, useRef, useState, type CSSProperties, type ReactNode } from "react";
import { AbsoluteFill, cancelRender, continueRender, delayRender, useCurrentFrame, useVideoConfig } from "remotion";
import * as PS from "@paper-design/shaders";
import { mountPreset, paramsToUniforms, shaderFrame, type PaperPreset } from "./paper-preset.js";

export const ShaderBackground: React.FC<{
  preset: PaperPreset;
  /** Logo or still for image presets, e.g. staticFile("logo.png"). */
  image?: string;
  /** Params that change over time; must be a pure function of seconds. */
  paramsAt?: (seconds: number) => Record<string, unknown>;
  minPixelRatio?: number;
  style?: CSSProperties;
  children?: ReactNode;
}> = ({ preset, image, paramsAt, minPixelRatio, style, children }) => {
  const frame = useCurrentFrame();
  const { fps } = useVideoConfig();
  const seconds = frame / fps;
  const host = useRef<HTMLDivElement>(null);
  const mount = useRef<PS.ShaderMount | null>(null);
  const [handle] = useState(() => delayRender(`Paper Shaders: ${preset.id}`));
  const latest = useRef({ seconds, paramsAt });
  latest.current = { seconds, paramsAt };

  const draw = (m: PS.ShaderMount) => {
    const { seconds: t, paramsAt: at } = latest.current;
    if (at) m.setUniforms(paramsToUniforms(PS, preset.shader, at(t)));
    m.setFrame(shaderFrame(preset, t));
  };

  // Mount once per preset; hold the render until images are loaded and the canvas has its size.
  useLayoutEffect(() => {
    let cancelled = false;
    mountPreset(PS, host.current!, preset, { image, minPixelRatio, seconds: latest.current.seconds })
      .then((m) => {
        if (cancelled) return m.dispose();
        mount.current = m;
        draw(m);
        continueRender(handle);
      })
      .catch((err) => cancelRender(err));
    return () => {
      cancelled = true;
      mount.current?.dispose();
      mount.current = null;
    };
  }, [preset, image, minPixelRatio]);

  // Draw synchronously after every render, before the browser paints the frame.
  useLayoutEffect(() => {
    if (mount.current) draw(mount.current);
  });

  return (
    <AbsoluteFill ref={host} style={style}>
      {children}
    </AbsoluteFill>
  );
};

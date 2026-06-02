import sharp from "sharp";

const DEFAULT_SCALE = 2;
const DEFAULT_THRESHOLD = 160;

export async function preprocessCaptchaImage({
  inputPath,
  scale = DEFAULT_SCALE,
  threshold = DEFAULT_THRESHOLD
}) {
  const source = sharp(inputPath);
  const metadata = await source.metadata();
  const width = Math.max(1, Math.round((metadata.width ?? 1) * scale));
  const height = Math.max(1, Math.round((metadata.height ?? 1) * scale));

  const buffer = await sharp(inputPath)
    .greyscale()
    .normalise()
    .resize({ width, height, fit: "fill" })
    .threshold(threshold)
    .png()
    .toBuffer();

  return {
    buffer,
    metadata: {
      width,
      height,
      format: "png"
    }
  };
}

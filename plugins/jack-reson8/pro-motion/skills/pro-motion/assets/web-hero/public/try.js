// "用我的照片"：在浏览器里把人抠出来（MediaPipe Selfie Segmenter，Apache-2.0），照片不上传。
// 只在用户选了照片之后才加载（运行时约 9.6 MB）。
const V = '0.10.21';
const CDN = `https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@${V}`;
let segmenter, pending;
function getSegmenter() { return pending ||= load().catch(e => { pending = null; throw e; }); }
async function load() {
  const { FilesetResolver, ImageSegmenter } = await import(`${CDN}/vision_bundle.mjs`);
  const files = await FilesetResolver.forVisionTasks(`${CDN}/wasm`);
  const opts = delegate => ({
    baseOptions: { modelAssetPath: new URL('/assets/models/selfie_segmenter.tflite', location.href).href, delegate },
    runningMode: 'IMAGE', outputConfidenceMasks: true, outputCategoryMask: false,
  });
  try { segmenter = await ImageSegmenter.createFromOptions(files, opts('GPU')); }
  catch { segmenter = await ImageSegmenter.createFromOptions(files, opts('CPU')); }
  return segmenter;
}

// 用户一按按钮就开始下运行时，挑照片的这几秒正好用来下载
export function preload() { getSegmenter().catch(() => {}); }

// 返回 { img, cut, cx, coverage }：img = 原图（≤1200px，已按 EXIF 转正），cut = 只留人的透明图，cx = 人的水平重心（0–1）
export async function cutOut(file) {
  const bmp = await createImageBitmap(file, { imageOrientation: 'from-image' }).catch(() => createImageBitmap(file));
  const s = Math.min(1, 1200 / Math.max(bmp.width, bmp.height));
  const w = Math.round(bmp.width * s), h = Math.round(bmp.height * s);
  const img = document.createElement('canvas'); img.width = w; img.height = h;
  img.getContext('2d').drawImage(bmp, 0, 0, w, h);

  const seg = await getSegmenter();
  const res = seg.segment(img);
  const mask = res.confidenceMasks[0];
  const mw = mask.width, mh = mask.height, conf = mask.getAsFloat32Array();
  // mask 放大到原图尺寸，置信度过一道 smoothstep 当 alpha
  const m = document.createElement('canvas'); m.width = mw; m.height = mh;
  const md = m.getContext('2d').createImageData(mw, mh);
  let sum = 0, sx = 0;
  for (let i = 0; i < conf.length; i++) {
    const t = Math.min(1, Math.max(0, (conf[i] - .35) / .3)), a = t * t * (3 - 2 * t);
    md.data[i * 4 + 3] = a * 255; sum += a; sx += a * (i % mw);
  }
  m.getContext('2d').putImageData(md, 0, 0);
  res.close?.();
  const cut = document.createElement('canvas'); cut.width = w; cut.height = h;
  const cx = cut.getContext('2d');
  cx.drawImage(img, 0, 0);
  cx.globalCompositeOperation = 'destination-in';
  cx.filter = 'blur(1px)';
  cx.drawImage(m, 0, 0, w, h);
  return { img, cut, cx: sum ? sx / sum / mw : .5, coverage: sum / conf.length };
}

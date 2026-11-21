import { extractTechnical, checkHreflang, checkImages, renderTechnicalMarkdown } from './page-technical.mjs';
import { checkMerchantSchema, renderMerchantSchema } from './merchant-schema.mjs';

export function parsePage(html, url) {
  const technical = extractTechnical(html, url);
  return { url, path: new URL(url).pathname, technical, title: technical.title,
    description: technical.description, h1: technical.h1,
    headings: technical.headings, jsonLd: technical.jsonLd };
}
export function runAudit(pages, { merchant = false } = {}) {
  return { scope: 'Supplied HTML only; no requests or provider calls.',
    hreflang: checkHreflang(pages), images: checkImages(pages),
    ...(merchant ? { merchant: checkMerchantSchema(pages) } : {}) };
}
export function renderAudit(report) {
  return '# Offline SEO source review\n\n' + renderTechnicalMarkdown(report.hreflang, report.images)
    + (report.merchant ? renderMerchantSchema(report.merchant) : '');
}

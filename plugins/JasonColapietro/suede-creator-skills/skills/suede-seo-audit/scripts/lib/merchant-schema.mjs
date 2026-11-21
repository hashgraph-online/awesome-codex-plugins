import { markdownText } from "./offline-reports.mjs";

const object = (v) => v !== null && typeof v === "object" && !Array.isArray(v);
const list = (v) => v == null ? [] : Array.isArray(v) ? v : [v];
const text = (v) => typeof v === "string" && v.trim() ? v.trim() : null;
const typeName = (v) => typeof v === "string" ? v.replace(/^https?:\/\/schema\.org\//, "") : "";
const hasType = (node, type) => list(node?.["@type"]).some((v) => typeName(v) === type);
const currencyCodes = new Set(Intl.supportedValuesOf("currency"));
const availabilityValues = new Set(["BackOrder", "Discontinued", "InStock", "InStoreOnly", "LimitedAvailability", "OnlineOnly", "OutOfStock", "PreOrder", "PreSale", "SoldOut"]);

function http(value, base) {
  if (typeof value !== "string" || !value.trim()) return null;
  try { const u = new URL(value, base); return /^https?:$/.test(u.protocol) && !u.username && !u.password ? u.href : null; }
  catch { return null; }
}

function graph(blocks, base) {
  const nodes = [];
  const ids = new Map();
  const seen = new WeakSet();
  const canonical = (v) => JSON.stringify(object(v) ? Object.fromEntries(Object.keys(v).sort().map((k) => [k, JSON.parse(canonical(v[k]))])) : v);
  function merge(left, right) {
    const node = { ...left }; let conflict = false;
    for (const [key, value] of Object.entries(right)) {
      if (key === "@id") { node[key] ??= value; continue; }
      if (key === "@type") { node[key] = [...new Set([...list(node[key]), ...list(value)])]; continue; }
      if (!(key in node)) node[key] = value;
      else if (canonical(node[key]) !== canonical(value)) conflict = true;
    }
    return { node, conflict };
  }
  function walk(value) {
    if (Array.isArray(value)) { value.forEach(walk); return; }
    if (!object(value) || seen.has(value)) return;
    seen.add(value); nodes.push(value);
    if (text(value["@id"]) && Object.keys(value).some((k) => k !== "@id")) {
      const id = http(value["@id"], base);
      if (id) {
        const prior = ids.get(id);
        const combined = prior ? merge(prior.node, value) : { node: value, conflict: false };
        ids.set(id, { node: combined.node, conflict: Boolean(prior?.conflict || combined.conflict) });
      }
    }
    Object.values(value).forEach(walk);
  }
  blocks.filter((b) => b.valid).forEach((b) => walk(b.value));
  const resolve = (value) => {
    if (!object(value)) return { node: value, unmeasured: false };
    const id = http(value["@id"], base);
    const definition = id && ids.get(id);
    if (definition) {
      const combined = merge(definition.node, value);
      const conflict = definition.conflict || combined.conflict;
      return { node: combined.node, unmeasured: conflict, conflict };
    }
    return { node: value, unmeasured: Object.keys(value).length === 1 && Boolean(value["@id"]) };
  };
  return { nodes, resolve };
}

function priceValid(value) {
  return (typeof value === "number" || (typeof value === "string" && /^\d+(?:\.\d+)?$/.test(value)))
    && Number.isFinite(Number(value)) && Number(value) > 0;
}

function gtinValid(value, size) {
  if (typeof value !== "string" || !/^\d+$/.test(value) || !(size ? value.length === size : [8, 12, 13, 14].includes(value.length))) return false;
  let sum = 0;
  for (let i = value.length - 2, weight = 3; i >= 0; i--, weight = weight === 3 ? 1 : 3) sum += Number(value[i]) * weight;
  return (10 - sum % 10) % 10 === Number(value.at(-1));
}

// Explicit merchant profile, not a general schema-validity verdict. Local JSON-LD
// definitions may be resolved, but this module never fetches an @id or image.
export function checkMerchantSchema(pages, { asOf = new Date().toISOString().slice(0, 10) } = {}) {
  return pages.map((page) => {
    const { nodes, resolve } = graph(page.jsonLd, page.url);
    const issues = [];
    let productCount = 0; let offerCount = 0;
    const visited = new Set();
    const add = (severity, code, product, field, message, remediation) => issues.push({ severity, code, product: text(product?.name) ?? "Unnamed Product", field, message, remediation });
    const unknown = (product, field, conflict = false) => add(conflict ? "warn" : "info", conflict ? "merchant-reference-conflict" : "merchant-reference-unmeasured", product, field,
      conflict ? `The ${field} ID has contradictory local definitions; its fields are unmeasured.` : `The ${field} reference has no local definition; its fields are unmeasured.`,
      conflict ? "Resolve the conflicting local ID definitions before assessing merchant fields." : "Include the referenced definition in the inspected JSON-LD or verify it separately; no remote reference was fetched.");
    for (const original of nodes.filter((n) => hasType(n, "Product"))) {
      const resolvedProduct = resolve(original);
      const product = resolvedProduct.node;
      const identity = http(product["@id"], page.url) ?? original;
      if (visited.has(identity)) continue;
      visited.add(identity);
      if (resolvedProduct.unmeasured) { unknown(product, "Product", resolvedProduct.conflict); continue; }
      const target = http(product.url ?? product["@id"], page.url);
      if (target && target !== page.url && Object.keys(product).every((k) => ["@type", "@id", "url"].includes(k))) {
        add("info", "merchant-variant-unmeasured", product, "url", `Off-page Product stub: ${target}.`, "Inspect that product or variant page before assessing its required merchant fields.");
        continue;
      }
      productCount++;
      if (!text(product.name)) add("error", "merchant-name", product, "name", "Merchant Product name is missing.", "Supply the actual product name shown to buyers.");
      const images = list(product.image);
      if (!images.length) add("error", "merchant-image", product, "image", "Merchant Product image is missing.", "Supply a crawlable product image URL or a locally defined ImageObject.");
      for (const image of images) {
        const resolved = resolve(image);
        if (resolved.unmeasured && (resolved.conflict || String(image["@id"]).includes("#"))) { unknown(product, "image", resolved.conflict); continue; }
        const value = object(resolved.node) ? resolved.node.contentUrl ?? resolved.node.url ?? resolved.node["@id"] : resolved.node;
        if (!http(value, page.url)) add("error", "merchant-image", product, "image", "Product image does not identify a supported HTTP(S) URL.", "Use the intended image URL; separately verify access, image quality and visible product correspondence.");
      }
      for (const key of ["gtin", "gtin8", "gtin12", "gtin13", "gtin14"]) {
        if (product[key] != null && !gtinValid(product[key], key === "gtin" ? null : Number(key.slice(4)))) add("warn", "merchant-gtin", product, key, `Supplied ${key} has invalid digits, length or check digit.`, "Correct the supplied identifier against the manufacturer's record; do not invent a GTIN.");
      }
      const offers = list(product.offers);
      if (!offers.length) add("error", "merchant-offers", product, "offers", "No merchant Offer is declared.", "Add an Offer for the actual purchasable product. Editorial product snippets use a different requirements profile.");
      for (const value of offers) {
        const resolved = resolve(value);
        if (resolved.unmeasured) { unknown(product, "offers", resolved.conflict); continue; }
        const offer = resolved.node;
        if (!object(offer) || !hasType(offer, "Offer")) {
          add("error", "merchant-offer-type", product, "offers", "Merchant listings require Offer; AggregateOffer alone is a product-snippet pattern.", "Use an Offer containing the active purchase price for the inspected product."); continue;
        }
        offerCount++;
        let price = offer.price; let currency = offer.priceCurrency;
        let priceMeasured = true;
        if (price === undefined) {
          const specs = list(offer.priceSpecification).map(resolve);
          const unresolved = specs.some((s) => s.unmeasured);
          const active = specs.filter((s) => !s.unmeasured).map((s) => s.node)
            .filter((s) => object(s) && (hasType(s, "UnitPriceSpecification") || hasType(s, "PriceSpecification")) && !s.validForMemberTier && s.priceType === undefined);
          if (!active.length && unresolved) { unknown(product, "priceSpecification", specs.some((s) => s.conflict)); priceMeasured = false; }
          if (active.length > 1) add("warn", "merchant-active-price", product, "priceSpecification", "Multiple active price specifications need purchase-state review.", "Identify the applicable active price; preserve legitimate member and strikethrough prices separately.");
          price = active[0]?.price; currency = active[0]?.priceCurrency;
        }
        if (priceMeasured && !priceValid(price)) add("error", "merchant-price", product, "offers.price", "Active merchant price must be a finite amount greater than zero, with a decimal point and no currency symbol.", "Supply the actual active purchase price; zero-price snippet rules do not establish merchant-listing eligibility.");
        if (priceMeasured && (typeof currency !== "string" || !currencyCodes.has(currency))) add("error", "merchant-currency", product, "offers.priceCurrency", "Active merchant price has no recognized ISO 4217 currency code.", "Supply the currency for that active price, for example USD; do not infer it from a currency symbol.");
        if (offer.url !== undefined && !http(offer.url, page.url)) add("error", "merchant-offer-url", product, "offers.url", "Supplied Offer URL must identify one HTTP(S) purchase page.", "Use a single purchase URL, retaining variant query parameters; omit an unnecessary URL rather than adding an array.");
        if (offer.availability == null) add("info", "merchant-availability-missing", product, "offers.availability", "Recommended availability is absent.", "Add the current product availability when it can be maintained accurately.");
        else if (!availabilityValues.has(typeName(offer.availability))) add("warn", "merchant-availability", product, "offers.availability", "Supplied availability is outside the supported merchant enumeration.", "Use the current supported availability value, such as InStock, BackOrder or OutOfStock.");
        if (offer.priceValidUntil !== undefined) {
          const date = offer.priceValidUntil;
          const valid = typeof date === "string" && /^\d{4}-\d\d-\d\d(?:T\d\d:\d\d(?::\d\d(?:\.\d+)?)?(?:Z|[+-]\d\d:\d\d)?)?$/.test(date) && Number.isFinite(Date.parse(date))
            && new Date(`${date.slice(0, 10)}T00:00:00Z`).toISOString().slice(0, 10) === date.slice(0, 10);
          if (!valid || date.slice(0, 10) < asOf) add("warn", "merchant-price-expiry", product, "offers.priceValidUntil", "Price validity date is malformed or before the review date.", "Review the active offer and update or remove an obsolete optional expiry date.");
        }
      }
    }
    const visitedGroups = new Set();
    for (const original of nodes.filter((n) => hasType(n, "ProductGroup"))) {
      const resolved = resolve(original);
      const group = resolved.node;
      const identity = http(group["@id"], page.url) ?? original;
      if (visitedGroups.has(identity)) continue;
      visitedGroups.add(identity);
      if (resolved.unmeasured) { unknown(group, "ProductGroup", resolved.conflict); continue; }
      const identifiers = new Map();
      const isVariantStub = (variant) => object(variant)
        && Object.keys(variant).every((k) => ["@type", "@id", "url"].includes(k))
        && Boolean(http(variant.url ?? variant["@id"], page.url));
      const variantEvidence = list(group.hasVariant).map(resolve);
      const variants = [];
      let variantsUnmeasured = false;
      for (const evidence of variantEvidence) {
        const variant = evidence.node;
        const stub = isVariantStub(variant);
        if (evidence.unmeasured || stub) {
          variantsUnmeasured = true;
          unknown(group, "hasVariant", evidence.conflict);
        } else if (object(variant)) variants.push(variant);
      }
      if (!text(group.name)) add("error", "merchant-group-name", group, "name", "Inspected ProductGroup has no name.", "Supply the shared product-group name and retain more specific names on full variant entities.");
      const relatedIds = [...new Set(variants.map((v) => text(v.inProductGroupWithID)).filter(Boolean))];
      if (!text(group.productGroupID) && (!variantEvidence.length || relatedIds.length > 1 || variants.some((v) => !text(v.inProductGroupWithID)) || (!variantsUnmeasured && relatedIds.length !== 1))) add("error", "merchant-group-id", group, "productGroupID", "No consistent group identifier is declared on the group or its inspected variants.", "Supply productGroupID or consistent inProductGroupWithID relationships using the actual group identifier.");
      for (const variant of variants) {
        const stub = isVariantStub(variant);
        if (!stub && !["sku", "gtin", "gtin8", "gtin12", "gtin13", "gtin14"].some((key) => text(variant[key]))) add("error", "merchant-variant-id-missing", variant, "sku/gtin", "Full variant has no SKU or GTIN identifier.", "Supply the actual unique variant identifier; URL-only off-page stubs remain unmeasured.");
        if (text(group.productGroupID) && text(variant.inProductGroupWithID) && group.productGroupID !== variant.inProductGroupWithID) add("warn", "merchant-group-id", variant, "inProductGroupWithID", "Variant group identifier disagrees with ProductGroup.productGroupID.", "Align the supplied variant relationship with its actual parent group.");
        for (const key of ["sku", "gtin", "gtin8", "gtin12", "gtin13", "gtin14"]) {
          if (!text(variant[key])) continue;
          const identity = http(variant.url ?? variant["@id"], page.url) ?? variant;
          const identifier = `${key}:${variant[key]}`;
          if (identifiers.has(identifier) && identifiers.get(identifier) !== identity) add("warn", "merchant-variant-identifier", variant, key, "Different inspected variants share the same supplied identifier.", "Check each variant's actual SKU or GTIN and correct reused identifiers; retain distinct selected-option URLs.");
          else identifiers.set(identifier, identity);
        }
      }
    }
    return { url: page.url, path: page.path, profile: "merchant", productCount, offerCount, issues };
  });
}

export function renderMerchantSchema(rows) {
  const text = markdownText;
  const lines = ["## 10. Merchant readiness profile", "", "Opt-in Product/Offer source checks. Editorial product snippets use different requirements. Live purchase-state accuracy, image access and Google rich-result eligibility remain unmeasured. No ratings, shipping policies or return policies were invented.", "",
    `Inspected ${rows.reduce((n, r) => n + r.productCount, 0)} Product entities and ${rows.reduce((n, r) => n + r.offerCount, 0)} Offers.`, "",
    "| Page URL | Product | Severity | Code | Field | Evidence | Next action |", "|---|---|---|---|---|---|---|"];
  for (const row of rows) for (const i of row.issues) lines.push(`| ${text(row.url)} | ${text(i.product)} | ${i.severity} | ${i.code} | ${i.field} | ${text(i.message)} | ${text(i.remediation)} |`);
  if (!rows.some((r) => r.issues.length)) lines.push("| – | – | – | – | – | No findings in the inspected merchant profile. | – |");
  return `${lines.join("\n")}\n`;
}

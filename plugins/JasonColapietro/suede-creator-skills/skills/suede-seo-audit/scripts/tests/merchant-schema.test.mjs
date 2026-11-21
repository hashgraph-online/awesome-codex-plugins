import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync, mkdirSync, writeFileSync, readFileSync, rmSync } from "node:fs";
import path from "node:path";
import { tmpdir } from "node:os";
import { parsePage, runAudit, renderAudit } from "../lib/audit.mjs";

const origin = "https://shop.test";
const product = (overrides = {}) => ({ "@type": "Product", name: "Handmade bowl", image: `${origin}/bowl.jpg`, offers: { "@type": "Offer", price: "24.50", priceCurrency: "USD", availability: "InStock" }, ...overrides });
function page(data, route = "/bowl") {
  return parsePage(`<html><head><title>Handmade bowl</title><script type="application/ld+json">${JSON.stringify(data)}</script></head><body><h1>Handmade bowl</h1><p>Handmade bowl costs 24.50 USD.</p></body></html>`, `${origin}${route}`);
}
function merchant(data) {
  const rows = runAudit([page(data)], { merchant: true }).merchant;
  assert.ok(Array.isArray(rows), "merchant schema profile is absent");
  return rows[0];
}
const codes = (row) => row.issues.map((i) => i.code);

test("merchant profile is opt-in and healthy direct offers need no invented ratings or purchase URL", () => {
  assert.equal(runAudit([page(product())]).merchant, undefined);
  const row = merchant(product());
  assert.equal(row.productCount, 1);
  assert.equal(row.offerCount, 1);
  assert.deepEqual(row.issues, []);
});

test("merchant requirements differ from editorial snippets and ordinary services remain unaffected", () => {
  const row = merchant({ "@type": "Product", aggregateRating: { ratingValue: 5, reviewCount: 2 } });
  for (const code of ["merchant-name", "merchant-image", "merchant-offers"]) assert.ok(codes(row).includes(code));
  const service = merchant({ "@type": "Service", name: "Consulting" });
  assert.equal(service.productCount, 0);
  assert.deepEqual(service.issues, []);
  assert.ok(codes(merchant(product({ offers: { "@type": "AggregateOffer", lowPrice: 20, highPrice: 30, priceCurrency: "USD" } }))).includes("merchant-offer-type"));
});

test("merchant price must be finite, positive and correctly formatted", () => {
  for (const price of [0, -1, "0.00", "-1", "1,000", "USD 20", "NaN", true, null, ""]) {
    const row = merchant(product({ offers: { "@type": "Offer", price, priceCurrency: "USD" } }));
    assert.ok(codes(row).includes("merchant-price"), JSON.stringify(price));
  }
});

test("active price specification works and direct price overrides specifications", () => {
  const active = { "@type": "UnitPriceSpecification", price: 24.50, priceCurrency: "USD" };
  const strike = { ...active, price: 40, priceType: "https://schema.org/StrikethroughPrice" };
  const member = { ...active, price: 20, validForMemberTier: { "@id": "#members" } };
  assert.ok(!codes(merchant(product({ offers: { "@type": "Offer", priceSpecification: [strike, member, active] } }))).includes("merchant-price"));
  assert.ok(codes(merchant(product({ offers: { "@type": "Offer", price: 0, priceCurrency: "USD", priceSpecification: active } }))).includes("merchant-price"));
  assert.ok(codes(merchant(product({ offers: { "@type": "Offer", priceSpecification: [strike, member] } }))).includes("merchant-price"));
});

test("generic price specifications work but selected-price currency cannot be borrowed", () => {
  const spec = { "@type": "PriceSpecification", price: 24.50, priceCurrency: "USD" };
  assert.ok(!codes(merchant(product({ offers: { "@type": "Offer", priceSpecification: spec } }))).includes("merchant-price"));
  const missing = { "@type": "UnitPriceSpecification", price: 24.50 };
  assert.ok(codes(merchant(product({ offers: { "@type": "Offer", priceCurrency: "USD", priceSpecification: missing } }))).includes("merchant-currency"));
  for (const priceType of ["https://schema.org/MSRP", "ListPrice", "StrikethroughPrice"]) {
    assert.ok(codes(merchant(product({ offers: { "@type": "Offer", priceSpecification: { ...spec, priceType } } }))).includes("merchant-price"));
  }
});

test("future datetime expiry is accepted and invalid or past dates are flagged", () => {
  for (const priceValidUntil of ["2026-12-31", "2026-12-31T23:59:59+00:00", "2026-12-31T23:59:59Z"]) {
    assert.ok(!codes(merchant(product({ offers: { ...product().offers, priceValidUntil } }))).includes("merchant-price-expiry"));
  }
  for (const priceValidUntil of ["2024-01-01", "2027-02-30", "2026-12-31T29:59:59Z"]) {
    assert.ok(codes(merchant(product({ offers: { ...product().offers, priceValidUntil } }))).includes("merchant-price-expiry"));
  }
});

test("missing or invalid currency and malformed optional offer URLs are diagnosed", () => {
  for (const currency of [undefined, "", "US", "ZZZ", 123]) {
    assert.ok(codes(merchant(product({ offers: { "@type": "Offer", price: 20, priceCurrency: currency } }))).includes("merchant-currency"));
  }
  for (const url of [[`${origin}/bowl`], "javascript:alert(1)", "https://user:pass@shop.test/bowl"]) {
    assert.ok(codes(merchant(product({ offers: { "@type": "Offer", price: 20, priceCurrency: "USD", url } }))).includes("merchant-offer-url"));
  }
});

test("availability is recommended while supplied availability values are validated", () => {
  const offer = { "@type": "Offer", price: 24.50, priceCurrency: "USD" };
  const missing = merchant(product({ offers: offer }));
  assert.equal(missing.issues.find((i) => i.code === "merchant-availability-missing").severity, "info");
  for (const availability of ["InStock", "BackOrder", "https://schema.org/OutOfStock"]) {
    assert.ok(!codes(merchant(product({ offers: { ...offer, availability } }))).includes("merchant-availability"));
  }
  assert.ok(codes(merchant(product({ offers: { ...offer, availability: "LotsAvailable" } }))).includes("merchant-availability"));
});

test("local graph Offer and ImageObject references resolve across blocks without fetching", () => {
  const graph = { "@graph": [product({ image: { "@id": "#photo" }, offers: { "@id": "#offer" } }),
    { "@id": "#photo", "@type": "ImageObject", contentUrl: `${origin}/bowl.jpg` },
    { "@id": "#offer", "@type": ["Offer"], price: 24.50, priceCurrency: "USD", availability: "https://schema.org/InStock" }] };
  assert.deepEqual(merchant(graph).issues, []);
  const html = `<head><title>Bowl</title><script type="application/ld+json">${JSON.stringify(product({ offers: { "@id": "#offer" } }))}</script><script type="application/ld+json">${JSON.stringify(graph["@graph"][2])}</script></head><body>Handmade bowl 24.50 USD</body>`;
  assert.deepEqual(runAudit([parsePage(html, `${origin}/bowl`)], { merchant: true }).merchant[0].issues, []);
});

test("compatible split ID declarations merge and contradictory definitions stay unmeasured", () => {
  const definitions = [product({ offers: { "@id": "#offer" } }), { "@id": "#offer", ...product().offers }, { "@id": "#offer", "@type": "Offer" }];
  assert.deepEqual(merchant(definitions).issues, []);
  const row = merchant([...definitions, { "@id": "#offer", "@type": "Offer", price: 999 }]);
  assert.ok(codes(row).includes("merchant-reference-conflict"));
  assert.ok(!codes(row).includes("merchant-price"));
});

test("split ProductGroup definitions are resolved once before required-field checks", () => {
  const data = [
    { "@id": "#group", "@type": "ProductGroup", name: "Bowls", productGroupID: "bowls", hasVariant: [product({ sku: "bowl-red" })] },
    { "@id": "#group", "@type": "ProductGroup" },
  ];
  assert.deepEqual(merchant(data).issues, []);
});

test("unresolved references are unmeasured rather than invented missing price fields", () => {
  for (const id of ["#missing-offer", "https://provider.test/offer"]) {
    const row = merchant(product({ offers: { "@id": id } }));
    assert.ok(codes(row).includes("merchant-reference-unmeasured"));
    assert.ok(!codes(row).includes("merchant-price"));
  }
});

test("unmeasured price specifications do not suppress supplied Offer-field defects", () => {
  const item = product({ offers: { "@type": "Offer", priceSpecification: { "@id": "#price" }, url: "javascript:alert(1)", availability: "LotsAvailable", priceValidUntil: "2024-01-01" } });
  for (const data of [item, [item,
    { "@id": "#price", "@type": "UnitPriceSpecification", price: 20, priceCurrency: "USD" },
    { "@id": "#price", "@type": "UnitPriceSpecification", price: 30, priceCurrency: "USD" },
  ]]) {
    const found = codes(merchant(data));
    for (const code of ["merchant-offer-url", "merchant-availability", "merchant-price-expiry"]) assert.ok(found.includes(code), code);
    assert.ok(!found.includes("merchant-price"));
    assert.ok(!found.includes("merchant-currency"));
  }
});

test("query-specific variants and off-page stubs are recognized without canonical mismatch noise", () => {
  const variants = [product({ "@id": "#red", url: `${origin}/bowl?color=red`, sku: "bowl-red", inProductGroupWithID: "bowl" }), { "@type": "Product", url: `${origin}/bowl?color=blue` }];
  const row = merchant({ "@type": "ProductGroup", name: "Handmade bowls", productGroupID: "bowl", hasVariant: variants });
  assert.equal(row.productCount, 1);
  assert.ok(codes(row).includes("merchant-variant-unmeasured"));
  assert.ok(!row.issues.some((i) => i.severity === "error"));
});

test("conflicting variant group IDs and duplicate SKUs are review findings", () => {
  const row = merchant({ "@type": "ProductGroup", productGroupID: "bowl", hasVariant: [
    product({ url: `${origin}/bowl?color=red`, sku: "same", inProductGroupWithID: "other" }),
    product({ url: `${origin}/bowl?color=blue`, sku: "same", inProductGroupWithID: "bowl" }),
  ] });
  assert.ok(codes(row).includes("merchant-group-id"));
  assert.ok(codes(row).includes("merchant-variant-identifier"));
});

test("inspected groups require a name, group relationship and distinct variant identifiers", () => {
  const row = merchant({ "@type": "ProductGroup", hasVariant: [product({ url: `${origin}/bowl?red` }), product({ url: `${origin}/bowl?blue` })] });
  for (const code of ["merchant-group-name", "merchant-group-id", "merchant-variant-id-missing"]) assert.ok(codes(row).includes(code));
});

test("supplied GTIN identifiers are checked including their check digit", () => {
  assert.ok(!codes(merchant(product({ gtin13: "4006381333931" }))).includes("merchant-gtin"));
  for (const gtin13 of ["4006381333932", "123", "abc"]) assert.ok(codes(merchant(product({ gtin13 }))).includes("merchant-gtin"));
});

test("merchant report includes actionable source findings and a clear profile scope", () => {
  const result = runAudit([page(product({ name: "" }))], { merchant: true });
  const md = renderAudit(result, { site: "shop.test", generatedAt: "2026-10-24" });
  assert.match(md, /## 10\. Merchant/);
  assert.match(md, /merchant-name/);
  assert.match(md, /eligibility.*unmeasured|unmeasured.*eligibility/i);
  assert.ok(result.merchant[0].issues.every((i) => i.remediation));
});

test("unresolved and conflicting group variants remain unmeasured", () => {
  const group = { '@type': 'ProductGroup', name: 'Bowls', hasVariant: { '@id': `${origin}/red` } };
  const unresolved = merchant(group);
  assert.ok(codes(unresolved).includes('merchant-reference-unmeasured'));
  assert.ok(!codes(unresolved).includes('merchant-group-id'));
  assert.ok(!codes(unresolved).includes('merchant-variant-id-missing'));
  const conflicting = merchant({ '@graph': [group,
    { '@id': `${origin}/red`, '@type': 'Product', name: 'Red bowl', inProductGroupWithID: 'a' },
    { '@id': `${origin}/red`, '@type': 'Product', name: 'Blue bowl', inProductGroupWithID: 'b' },
  ] });
  assert.ok(codes(conflicting).includes('merchant-reference-conflict'));
  assert.ok(!codes(conflicting).includes('merchant-group-id'));
  assert.ok(!codes(conflicting).includes('merchant-variant-id-missing'));
  const mixed = merchant({ ...group, hasVariant: [
    product({ sku: 'known', inProductGroupWithID: 'bowls' }), { '@id': `${origin}/unknown` },
  ] });
  assert.ok(codes(mixed).includes('merchant-reference-unmeasured'));
  assert.ok(!codes(mixed).includes('merchant-group-id'));
});

test("malformed inline variants and known relationship gaps are not hidden by unknown references", () => {
  for (const variant of [{}, { '@type': 'Product' }]) {
    const row = merchant({ '@type': 'ProductGroup', name: 'Bowls', hasVariant: variant });
    assert.ok(codes(row).includes('merchant-group-id'));
    assert.ok(codes(row).includes('merchant-variant-id-missing'));
    assert.ok(!codes(row).includes('merchant-reference-unmeasured'));
  }
  const mixed = merchant({ '@type': 'ProductGroup', name: 'Bowls', hasVariant: [
    product({ sku: 'known' }), { '@id': `${origin}/unknown` },
  ] });
  assert.ok(codes(mixed).includes('merchant-reference-unmeasured'));
  assert.ok(codes(mixed).includes('merchant-group-id'));
});

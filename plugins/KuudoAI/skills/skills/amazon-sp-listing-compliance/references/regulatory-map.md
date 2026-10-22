# Regulatory map for listing compliance

*Last checked 2026-09-16 against Seller Assistant answers, with help-hub references as returned. Adapted from Amazon Selling Partner's `listing-compliance` skill (Apache-2.0).*

Orientation, not authority. Use it to classify a product in Step 1 and to draft the seller questions in Step 4. Confirm the specific category through Seller Assistant in Step 5 when that step is warranted and available, and prefer that answer where the two disagree. Help-hub references are in parentheses; the FDA section came back from Seller Assistant without links.

## Section index — read only what applies

Always read **Every listing** and **Category-level**. Then read only the buckets the product plausibly hits. Do not load this file whole; each section stands alone.

A few rules live outside the bucket their product name suggests — lasers sit under FDA, magnet sets under CPSC. Follow this table, not the section title, and when a product could sit in two buckets read both.

| Section | Read it when the product… |
|---|---|
| Every listing | always |
| Category-level | always (GTIN, gating, condition) |
| FDA | is ingested, applied to the body, is a medical device, **or is a laser product** |
| EPA | is a chemical, contains PFAS/BPA, or claims to kill/repel pests or microbes |
| CPSC | targets children 12 and under, **or is a novelty magnet set** (prohibited — see this section) |
| FCC | transmits or receives radio (Wi-Fi, Bluetooth, RF) |
| FTC | uses endorsements, testimonials, or "Made in USA" |
| Required on-listing statements and disclosures | is a vehicle part, lighting, appliance, plumbing, textile, furniture, bedding, fur, or wool |
| Other product-specific | is a refrigerator water filter (lasers → **FDA**; magnet sets → **CPSC**) |
| Cross-cutting | always skim if unsure which bucket applies |
| Enforcement | the product is borderline and you need the consequence |

## Every listing (GXPFG3RRZB9WFPJE; selling policies GSNV3657R94YP9DZ)

- Lawful product, compliant with the seller agreement and Amazon policies.
- Attributes: model or part number, manufacturer or brand name, compliance information.
- Consistent product details and list prices across duplicate listings of the same product.
- Images showing all sides of the product and its packaging. The Add Products tool blocks submission until main-image defects are resolved.
- Certain categories also require accredited-lab test reports, a Certificate of Insurance via Business Insurance verification, a Children's Product Certificate, and permanently affixed hazard warnings.
- Non-compliance (missing or inaccurate compliance info, failed testing, prohibited or restricted items, image issues) leads to suppression or removal.

## Category-level (G200301050, G200316110)

| Rule | Applies to | Seller must supply |
|------|-----------|--------------------|
| Prior approval (gated category) | Health & Personal Care, Beauty, Jewelry, Watches, and others | Whether approval is already held; otherwise the apply-to-sell path |
| GTIN required | Most categories | UPC / EAN / ISBN / JAN, or an approved exemption |
| Condition guidelines | Category-specific | Condition (new, used, refurbished) and that it meets the category's definition |

## FDA (no help-hub links returned)

| Product type | Rules | Documents / tests the seller must have |
|-------------|-------|----------------------------------------|
| Food & beverage | FD&C Act Title 21; 21 CFR 101 (labeling), 110 (GMP), 117 (preventive controls) | Compliant labeling; GMP |
| Infant formula | FD&C Act § 412; 21 CFR 106 (manufacturing, quality control, records, registration and notification) and 107 (labeling, nutrients). FDA does **not** approve infant formula before sale | Manufacturer registration with FDA, and a new-infant-formula notification submitted at least 90 days before marketing. A seller who isn't the manufacturer needs the manufacturer's confirmation of both. There is no "FDA approval" document to ask for |
| Baby food | Thermally processed low-acid food standards | Process compliance |
| Organic claims | 7 CFR 205 | Organic certification |
| Cosmetics (MoCRA 2022) | FDA facility registration and product listing; safety substantiation; GMP (ISO 22716:2007 or equivalent); serious adverse-event reporting within 15 business days; full labeling | Registration, safety records, GMP. Prohibited: mercury, formaldehyde-releasing agents, methylene glycol, permanent lash/brow dyes, plastic microbeads |
| Medical devices | 21 CFR 801 (labeling), 807 (registration and listing), 807 Subpart E 510(k), 814 PMA. **Find the product code and classification first:** most Class I devices and some Class II devices are exempt from 510(k); non-exempt Class I/II devices need 510(k) clearance (or De Novo); Class III needs PMA | Establishment-registration and device-listing evidence, and UDI on labels where required. Then only what the classification requires: the 510(k) letter or PMA approval, or the exemption citation (the 21 CFR classification regulation) for an exempt device. Don't hold an exempt device for a missing 510(k). Rx devices only via the Professional Healthcare (PHC) program |
| OTC oral medications | 16 CFR 1700 (child-resistant packaging), 21 CFR 201 (labeling), 207 Subpart C (NDC), 210/211 (drug GMP) | API assay, heavy-metals (Cd, Pb, As, Hg), microbial testing, GMP certification |
| Personal lubricants | 21 CFR 807 registration and listing; 510(k) | Registration and clearance |
| Laser products (G201707070) | State hazard class and power output in mW; max Class IIIA (Class I for children's toys) | Independent-lab verification per FDA standards |

## EPA

- TSCA for chemical products, including items containing PFAS.
- BPA restricted in bottles and cups for children 3 and under in some states.
- Pesticides and antimicrobial claims need FIFRA plus state pesticide registration and labeling (G201707070).

## CPSC (children's products, 12 and under)

- CPSIA lead and phthalate limits; Flammable Fabrics Act for children's sleepwear; third-party testing by CPSC-accredited labs; Children's Product Certificate.
- Toys or games with small parts need CPSIA choking-hazard warnings on the listing (G201707090).
- Novelty strong-magnet sets marketed for entertainment are prohibited, including named brands Buckyballs, Neocubes, Nanodots, Zen magnets (G201707070).
- Exposed-cord window coverings must meet ANSI/WCMA A.100.1 (G201707070).

## FCC

- Radio-frequency devices need FCC compliance and may need an FCC ID or authorization (G201707070).

## FTC

- Testimonials, endorsements, feedback and reviews follow the FTC Guides: disclose material connections; never pay for reviews or offer gifts or refunds for review removal (G201707070).
- "Native American", "Indian", or tribal names may not imply tribal-made origin unless true, per the Indian Arts and Crafts Acts of 1935 and 1990 (G201707070).

## Required on-listing statements and disclosures (G201707090)

| Product type | Required statement |
|-------------|--------------------|
| Engines, aftermarket auto parts, catalytic converters, air cleaners, gas cans | CARB Executive Order number or certification permitting sale into California |
| Products with California-listed chemicals | Link to the "About California Proposition 65" page |
| Appliances, lighting, plumbing | EnergyGuide (yellow) or Lighting Facts (white) label, encircled-E energy icon for certain lighting, water-use information for plumbing |
| Textiles (bedding, clothing, tablecloths, towels) | Country of origin; generic fiber names and percentages by weight (5% or more) in order of predominance; "rayon derived from bamboo" / "azlon derived from soy", never bare "bamboo" or "soy" |
| Upholstered furniture, bedding, mattresses | State content-labeling laws: minimum label and font size, filler materials with percentages, Uniform Registry Number or sterilization permit, state registration for manufacturers, wholesalers, importers, distributors |
| Wearable fur | Animal name; country preceded by "Fur Origin"; statements if used, damaged, bleached, dyed, or scrap; faux fur labeled "faux" |
| Wool | Country of origin; fiber percentages; new versus recycled |

## Other product-specific (G201707070)

- Refrigerator replacement water filters: certified to NSF/ANSI-42 or higher by an accredited independent lab (NSF, WQA, IAPMO); reduction claims displayed accurately.

## Cross-cutting

- No "FDA approved" claim without actual approval.
- Third-party testing for most regulated products.
- Labeling carries manufacturer info, warnings, and compliance marks.
- Documents must be authentic, unmodified, and in English.
- State-specific rules (California, Utah, and others) may apply.

## Enforcement (GXMGGPL6LC4CVXHT)

Violations may lead to suspension or termination of selling privileges, destruction of fulfillment-center inventory without reimbursement, inventory return, permanent withholding of payments, and legal action (civil or criminal penalties, forfeiture of goods). Listing a restricted product, even unintentionally, may result in listing removal, account suspension, or loss of selling privileges. State this once in the checklist for a borderline product.

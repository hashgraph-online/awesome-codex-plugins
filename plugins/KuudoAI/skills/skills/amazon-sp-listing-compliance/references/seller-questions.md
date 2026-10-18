# Seller questions (Step 4)

*Adapted from Amazon Selling Partner's `listing-compliance` skill (Apache-2.0).*

Ask **once**, grouped, and include only the blocks that the Step 1 classification made relevant. Read only those blocks — each `##` block below stands alone, and loading all of them costs tokens you replay on every later turn. "Always ask" plus your matching buckets is enough. Use the structured question tool where available; otherwise a single message with numbered items. Record every answer as met, unmet, or not applicable. "I don't know" is unmet.

## Always ask

1. What exactly is the product, and who is it for? Is it intended for children 12 and under, or infants 3 and under?
2. Do you have a GTIN (UPC / EAN / ISBN / JAN) for it, or an approved GTIN exemption?
3. What condition are you listing: new, used, or refurbished?
4. Do you already hold approval to sell in this category (if it is gated)?

## Ask when the product is ingestible, applied to the body, or a device (FDA)

5. Full ingredient or material list?
6. Which FDA registrations or clearances apply and do you hold: facility registration and product listing (cosmetics); for devices, the product code and classification, then the 510(k), PMA, or the 510(k) exemption that applies; for infant formula, the manufacturer's FDA registration and new-formula notification; NDC (OTC drugs)?
7. Do you have GMP documentation and, for OTC drugs, API / heavy-metal / microbial test reports?
8. Does the packaging or listing make any "FDA approved" or health claim?

## Ask when the product is a chemical, contains PFAS/BPA, or makes antimicrobial claims (EPA)

9. Does it contain PFAS or BPA? Is it a bottle or cup for children 3 and under?
10. Does it claim to kill, repel, or control pests or microbes? If so, what is the FIFRA / state registration?

## Ask when the product targets children 12 and under (CPSC)

11. Do you have a Children's Product Certificate and CPSC-accredited lab test reports (lead, phthalates, flammability as applicable)?
12. Does it have small parts (choking hazard warning needed) or strong magnets?
13. Is it sleepwear, or a corded window covering?

## Ask when the product has wireless, radio, or electronic function (FCC)

14. Does it transmit or receive radio signals (Wi-Fi, Bluetooth, RF)? What is the FCC ID or authorization?

## Ask when the product is a vehicle part, lighting, appliance, plumbing, textile, furniture, bedding, fur, or wool (disclosures)

15. Auto parts, engines, gas cans: what is the CARB Executive Order number?
16. Does it contain a California Prop 65 listed chemical?
17. Appliance / lighting / plumbing: do you have the EnergyGuide, Lighting Facts, or water-use information?
18. Textiles: country of origin and fiber content by percentage?
19. Upholstered furniture, bedding, mattress: filler content percentages and Uniform Registry Number or sterilization permit?
20. Fur: animal, fur origin country, and treatment (dyed, bleached, scrap)? Faux fur labeled as faux?
21. Wool: origin, fiber percentages, new or recycled?

## Ask when the product is a laser, water filter, or uses reviews/endorsements in content

22. Laser: hazard class and power output in mW, and the independent-lab verification?
23. Refrigerator water filter: NSF/ANSI-42 certification body and reduction claims?
24. Does the listing content include testimonials or endorsements with any material connection, or Native American / tribal terminology?

## Recording rule

For each item record `met` (seller confirmed and, where relevant, has the document), `unmet` (missing, or "I don't know"), or `n/a` (bucket does not apply). The checklist in Step 6 is built from these states plus the Seller Assistant confirmation and the gating result. Never fill a value the seller did not give.

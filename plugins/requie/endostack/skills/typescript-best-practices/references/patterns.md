# TypeScript patterns

One example per rule in [../SKILL.md](../SKILL.md), numbered to match. The domain is a small parcel-shipping service. The schema examples use zod because many repos already have it; use whatever validation library your repo already depends on.

## 1. Tagged unions

Don't:

```ts
type Quote = {
	pending: boolean;
	price?: number;
	failureReason?: string;
};
```

`{ pending: false }` with neither field set compiles, and so does `{ pending: true, failureReason: "x" }`.

Do:

```ts
type Quote =
	| { kind: "pending" }
	| { kind: "priced"; priceCents: number; carrier: string }
	| { kind: "failed"; reason: string };
```

## 2. Branded primitives

```ts
type TrackingNumber = string & { readonly __brand: "TrackingNumber" };

function isTrackingNumber(value: string): value is TrackingNumber {
	return /^[A-Z]{2}\d{9}[A-Z]{2}$/.test(value);
}

function parseTrackingNumber(value: string): TrackingNumber {
	if (!isTrackingNumber(value)) {
		throw new Error(`invalid tracking number: ${JSON.stringify(value)}`);
	}
	return value;
}

// Downstream code trusts the brand and does not re-check.
function trackingUrl(id: TrackingNumber): string {
	return `/track/${id}`;
}
```

Don't: `const id = req.query.t as TrackingNumber;`. The brand now claims a check that never ran.

## 3. Unconstructible illegal values

```ts
type NonEmpty<T> = [T, ...T[]];

function cheapestCarrier(quotes: NonEmpty<PricedQuote>): PricedQuote {
	return quotes.reduce((best, q) => (q.priceCents < best.priceCents ? q : best));
}

function isNonEmpty<T>(items: T[]): items is NonEmpty<T> {
	return items.length > 0;
}

type DimensionPairs = Array<[label: string, centimeters: number]>;

type Minutes = number & { readonly __brand: "Minutes" };
type PickupWindow = { start: Date; length: Minutes };

function windowEnd(w: PickupWindow): Date {
	return new Date(w.start.getTime() + w.length * 60_000);
}
```

Don't: `{ start: Date; end: Date } // end must be after start`. Nothing enforces the comment.

## 4. Simplest total type

This is fine as a plain array, because a sum over nothing is zero:

```ts
function totalWeightGrams(parcels: Parcel[]): number {
	return parcels.reduce((sum, p) => sum + p.weightGrams, 0);
}
```

This one lies:

```ts
function heaviest(parcels: Parcel[]): Parcel {
	return [...parcels].sort((a, b) => b.weightGrams - a.weightGrams)[0]!;
}
```

Fix it by taking `NonEmpty<Parcel>`, or by returning `Parcel | undefined`. Callers holding a plain array call `isNonEmpty` once.

## 5. `unknown` for external data

Don't:

```ts
window.addEventListener("message", (e: MessageEvent<any>) => {
	applyLabel(e.data.labelId);
});
```

Do:

```ts
window.addEventListener("message", (e: MessageEvent<unknown>) => {
	if (e.origin !== LABEL_PRINTER_ORIGIN) return;
	const msg = LabelMessage.safeParse(e.data);
	if (!msg.success) return;
	applyLabel(msg.data.labelId);
});
```

The origin check matters as much as the type: any page can post a message to the window.

## 6. Schemas first

```ts
import { z } from "zod";

const Address = z.object({
	line1: z.string().min(1),
	postcode: z.string().regex(/^[A-Z0-9 ]{3,10}$/),
	country: z.string().length(2),
});
type Address = z.infer<typeof Address>;

const result = Address.safeParse(formValues);
if (!result.success) showErrors(result.error);
```

When the type came first, tie the schema to it so a looser schema fails to compile:

```ts
const CarrierConfig: z.ZodType<CarrierConfigType> = z.object({
	name: z.string(),
	maxWeightGrams: z.number().int().positive(),
});
```

## 7. Assertions only after validation

Don't:

```ts
const rate = (await res.json()) as RateResponse;
```

Don't write a guard that only checks one field either:

```ts
function isRateResponse(x: any): x is RateResponse {
	return "priceCents" in x;
}
```

Do:

```ts
const rate = RateResponse.parse(await res.json());
```

## 8. Narrowing with `in`

```ts
type Box = { lengthCm: number; widthCm: number; heightCm: number };
type Tube = { lengthCm: number; diameterCm: number };

function volumeCm3(p: Box | Tube): number {
	if ("diameterCm" in p) {
		return Math.PI * (p.diameterCm / 2) ** 2 * p.lengthCm;
	}
	return p.lengthCm * p.widthCm * p.heightCm;
}
```

## 9. Guards on the tag

```ts
function isPriced(q: Quote): q is Extract<Quote, { kind: "priced" }> {
	return q.kind === "priced";
}
```

## 10. Exhaustive switches

Value-returning:

```ts
function quoteLabel(q: Quote): string {
	switch (q.kind) {
		case "pending":
			return "Fetching rates";
		case "priced":
			return `${q.carrier}: ${formatCents(q.priceCents)}`;
		case "failed":
			return `No rate: ${q.reason}`;
		default: {
			const unhandled: never = q;
			return unhandled;
		}
	}
}
```

Statement form:

```ts
switch (q.kind) {
	case "pending":
		spinner.show();
		break;
	case "priced":
	case "failed":
		spinner.hide();
		break;
	default: {
		const unhandled: never = q;
		void unhandled;
	}
}
```

## 11. `satisfies` for literals

Don't: `const limits = { parcelGrams: 30000, palletGrams: 1000000 } as Limits;`. A typo in a key is accepted.

Do:

```ts
const limits = {
	parcelGrams: 30_000,
	palletGrams: 1_000_000,
} satisfies Limits;
```

## 12. Parse once at the boundary

```ts
app.post("/shipments", async (req, res) => {
	const parsed = CreateShipment.safeParse(req.body);
	if (!parsed.success) return res.status(400).json(parsed.error.flatten());
	const shipment = await createShipment(parsed.data);
	res.status(201).json({ id: shipment.id });
});

// createShipment takes the domain type and never sees req.body.
async function createShipment(input: CreateShipment): Promise<Shipment> {
	// ...
}

function loadDraft(raw: string): Draft | undefined {
	try {
		return DraftV2.parse(JSON.parse(raw));
	} catch {
		return undefined;
	}
}
```

For wire messages, use the schema's passthrough or non-strict mode so a newer sender's extra fields do not break an older reader.

## 13. Derive from generated types

Don't redeclare a shape the generated client already has:

```ts
interface ShipmentRow {
	id: string;
	status: string;
	carrier: string;
}
```

Do:

```ts
import type { components } from "./generated/openapi";

type ShipmentSummary = Pick<components["schemas"]["Shipment"], "id" | "status" | "carrier">;

function renderRow(s: ShipmentSummary): string {
	return `${s.id} ${s.status} ${s.carrier}`;
}
```

## 14. Object parameters

Don't:

```ts
schedulePickup(depotId, customerId, startsAt, 120, true);
```

`depotId` and `customerId` are both strings, so swapping them compiles.

Do:

```ts
schedulePickup({
	depotId,
	customerId,
	window: { start: startsAt, length: minutes(120) },
	signatureRequired: true,
});
```

## 15. Real tests

Don't mock the database driver to return a canned row and then assert that your code called `query` once. Start the database the repo's dev setup provides, insert a fixture row, call the function, and assert on what it returns. Turn on the test runner's leak detection (open handles, pending timers) so a forgotten connection fails the suite.

## 16. Structured telemetry

Don't:

```ts
console.log("label failed", err);
```

Do:

```ts
log.warn("label.render_failed", {
	shipmentId: shipment.id,
	carrier: shipment.carrier,
	templateVersion,
	errorCode: err.code,
});
```

The shipment id alone now finds every related event. Leave out the address and any API key the carrier client holds.

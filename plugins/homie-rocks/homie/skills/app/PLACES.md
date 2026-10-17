# Build a place people recognize

Use this with APPS.md and TOOLS.md. Six place builds exposed the same rule:
make the owner's dream visible, with one trusted operation behind every action.

1. **Start with their paragraph.** Quote the owner's actual words in CODEX.md,
   including sensory details and operating rules. Write one executable need per
   clause. Describe Scene as data: “held = white ball; confirmed = gold; mine =
   gold ring; empty capacity = empty pegs.” List phone, wall, signed-in staff,
   customer AI and owner AI with their addresses and actions. Record what is
   simulated, evidence viewports and who reviewed it. Local review is not independent.
2. **Make records visible.** Give each meaningful record an object, each state a
   material, and the visitor's object a clear marker. Arrivals pop and chime;
   outcomes become bags, cups or flags. Empty capacity can be negative space.
3. **Spend geometry where it reads.** Use one layout curve for paths, trees and
   objects. Add a gradient sky shader and sun, fog matching the horizon, terrain
   vertex colours by zone, and seeded low-poly local vegetation. Animate water
   and a flag in vertex shaders; avoid recomputing a large mesh's normals every
   frame. Ease role-specific cameras with `1 - Math.exp(-dt * 4)`. Cap pixel
   ratio on phones, pause hidden frames, respect reduced motion. Generate a
   filtered noise ambient bed after the first sound opt-in; its gain follows the
   scene. Compose a share card from the live scene and actual outcome.
4. **One set of rules.** Put validation and transitions in `domain.ts`; the view
   may preview them, but a `defineTool` handler decides and saves. Screens call
   `createAppTools().call`, AIs call the same definition over MCP. Use strict
   schemas, bounded inputs, versioned writes with revalidation on conflict, and
   a caller-generated request ID. A repeated ID with different data is refused.
   Do not rebuild the operation with browser record writes or a custom route.
5. **Plan the AI's whole visit.** Provide `place_info` (“Call this first”: rules,
   availability, prices, notice), `place_book` (all choices in one call, bounded
   enums from config, a private management credential and a `next` sentence),
   and `place_booking` (owner-authorized lookup/change/cancel). Never expose
   management credentials in public records. Owner tools read an outbox, mark
   messages sent, consume event feeds, and repeat next month by a calendar rule.
   Homie composes; the owner's AI sends through its own connector. A repeat
   invites past visitors; it never silently enrols them.
6. **Operate from one config.** Put the place's IANA zone, schedule rule, capacity,
   prices, add-ons and notice in one config. Derive UI, tools and `shop.json` from
   it during build. Do not maintain a second price list. Model holds → confirm →
   scheduled release, with fixed spot IDs and version checks on reuse. Group
   allocation must be atomic, never a loop that reports partial success. Use the
   toolkit's booking capacity for paid inventory. HANDOVER.md says what runs
   where, the monthly rhythm, how to connect an AI, what to do when the owner
   leaves, and which integrations are still unproven.

## Small working boundaries

The examples use the installed toolkit's exports. Declare `reserve` in `tools/`;
this small example reserves one whole slot for a signed-in account. Keep the
public collection a projection without account IDs or secrets. A production
paid slot uses the shop booking system, not a second ledger.

```ts
import { defineTool } from '@homie-rocks/studio/tools';
export default defineTool<{ slot: string; request: string }>({
  name: 'reserve', description: 'Reserve one slot; repeat the same request safely.',
  audience: 'signed-in',
  inputSchema: {
    type: 'object', additionalProperties: false, required: ['slot', 'request'],
    properties: {
      slot: { type: 'string', enum: ['morning', 'afternoon'] },
      request: { type: 'string', pattern: '^[a-f0-9]{32}$' }
    }
  },
  async handler(input, ctx) {
    const owner = ctx.caller.id;
    const key = 'slot:' + input.slot;
    const old = await ctx.database.getVersioned(key);
    if (old) {
      const saved = old.value as { owner: string; request: string };
      if (saved.owner === owner && saved.request === input.request) return { booked: true };
      return { booked: false, next: 'That slot is full. No place has been taken.' };
    }
    const result = await ctx.database.put(key, { owner, request: input.request }, { version: 0 });
    return { booked: result.ok, next: result.ok ? 'Your place is reserved.' : 'That slot filled. Choose another.' };
  }
});
```

```ts
import { createAppTools, createAppContext, createAppRecords } from '@homie-rocks/studio/apps';
const tools = createAppTools();
const context = createAppContext();
const self = await context.ready; // self.url is public; it contains no private access link
const records = createAppRecords<{ status: string }>({ collection: 'spots' });
const refresh = async () => {
  const rows = await records.list();
  document.querySelector('output')!.textContent = `${rows.length} places · ${self.url}`;
};
const stop = records.subscribe(() => { void refresh(); });
await refresh();
// In the visitor's click handler, preserve request across network retries:
const request = crypto.randomUUID().replaceAll('-', '');
await tools.call('reserve', { slot: 'morning', request });
// On unmount: stop(); records.dispose(); context.dispose(); tools.dispose();
```

Build the controls first: an area menu is the primary navigation, and tapping a
3D object selects the same area. Catch renderer creation failure and context loss;
keep every booking/control usable without WebGL. Refusals are human sentences
that say what happened. Prove refusals by bypassing disabled controls, race two
browsers for the last seat, reload and restart, and run with WebGL unavailable.
Document the exact commands and results; an empty assertion list is not proof.

## Do not teach the mistakes

- No booking codes in public collections or anonymous edits of arbitrary bookings.
  Bind tickets to their account/seat, or verify a secret only the booker holds.
- No public staff console. Use a signed-in role and check it on the server.
  Label an intentionally public simulator in both UI and Codex.
- Never interpolate visitor text into `innerHTML`: a stored XSS reached a staff
  tablet in the study. Use `textContent` for names, contacts, notices and outbox text.
- Never issue an “official receipt” for an unpaid donation. Record a pledge as a
  pledge; count a paid gift only after a verified, deduplicated `order.paid` event,
  with the gift's ID as its reference.
- No fixed UTC offsets or one hard-coded event date. Use IANA zones and recurring
  calendar rules; carry the same occurrence into site copy and all screens.
- No sleep-and-retry event arrays or staff-device cron jobs. Use durable functions,
  version checks, declared feeds and the server scheduler.
- No live-only assets. Commit every asset the site serves, with its provenance,
  and verify a clean checkout can build it. Declare only packages actually used.
- No invented reviews, impact figures or verification. Label estimates and test
  payments honestly; remove stale workaround claims when upgrading.

## Booking toolkit and customer-AI arguments

Use declared booking slots and resources instead of duplicating capacity logic.
`studio_book` accepts `slot` or `time`, `resource`, `preferredResource` or
`preferred_resource`, and `addons`, `addOns` or `add-ons` as an array of IDs or an
object of quantities. Contradictory aliases are refused. Use the same option and
resource IDs in `createBookingChoices` on the phone. A booking may allocate
multiple resource components, with skills, attributes and capacity checked by
the server. Use the app's IANA `timeZone` and `ctx.bookings.calendar` for dated or
multi-day seasons. Public holds need a stable ID, bounded expiry and a private
management token for anonymous customers.

Pass the app's booking reference to `shop.book` or MCP `studio_checkout`. For
variable deposits use an amount-based link and validate the paid amount against
the saved booking. Declare `booking.slots_need_payment_links` so the owner's AI
can prepare links for newly rolled dates through Stripe's official plugin.
Use `shop observe` to record plugin responses, then verify and build.

The toolkit's `docs/toolkit-batch.md` documents resource declarations, install
surfaces, private frames, concept previews, example forks and isolated live-site
checks. Record IDs belong at the top level of `ctx.records`/`app_records`
arguments, alongside `app` and `collection`.

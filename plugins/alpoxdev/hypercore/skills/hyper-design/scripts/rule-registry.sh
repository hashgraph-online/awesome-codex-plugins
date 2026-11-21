#!/usr/bin/env bash
# Canonical machine-readable slop-rule registry shared by the detector and the waiver validator.
# Fields (tab separated): id, defaultSeverity, class, engines, evidence, action, fix, evidenceLimit,
# exceptionChecks, dispositionPolicy, clusterKey, immediateTier, matcher source, matcher flags.
# An engines value of `motion-context` marks a project-wide rule the detector evaluates over the
# whole scan instead of the per-file matcher table, so no engine selects it for a source scan.
set -euo pipefail

# rule_registry_rows prints every registry row as tab-separated fields in declaration order.
rule_registry_rows() {
  cat <<'RULES_TABLE'
surface.gradient-text	P2	default-risk	css	Gradient-clipped text source signature	review	Preserve explicit brand/reference typography; otherwise use a confirmed solid token.	Static source signatures require context before remediation.	explicit brand gradient	review	surface.gradient-text	0	(?:background-clip\s*:\s*text|-webkit-background-clip\s*:\s*text|bg-clip-text)	gi
surface.purple-gradient	P2	default-risk	css	Purple-to-blue/pink gradient-like token sequence	review	Preserve documented brand gradients; otherwise review a confirmed solid token.	Static source signatures require context before remediation.	explicit brand gradient	review	surface.purple-gradient	0	(?:purple|violet|fuchsia|#(?:7c3aed|8b5cf6|a855f7|c026d3)).{0,100}(?:blue|pink|cyan|#(?:2563eb|3b82f6|ec4899))	gi
motion.transition-all	P2	universal	css	Broad transition declaration	replace	Replace all with only the properties that actually change.	Static source signatures require context before remediation.		autofix-safe	motion-broad-transition	0	(?:transition\s*:\s*all\b|\btransition-all\b)	gi
motion.layout-property	P1	universal	css	Layout property animation signature	review	Prefer transform/opacity only when behavior remains equivalent.	Static source signatures require context before remediation.		review	motion.layout-property	0	(?:transition(?:-property)?\s*:[^;]*(?:top|left|width|height|margin|padding)|(?:animate|transition)[\w:-]*\([^)]*(?:top|left|width|height|margin|padding))	gi
surface.thick-side-stripe	P2	default-risk	css	Thick colored side-border signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.thick-side-stripe	0	border-(?:left|inline-start)(?:-width)?\s*:\s*(?:[5-9]|\d{2,})px|\bborder-l-(?:4|8)\b	gi
surface.thin-side-stripe	P2	default-risk	css	Thin one-sided border signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.thin-side-stripe	0	border-(?:left|right|inline-start|inline-end)(?:-width)?\s*:\s*(?:1|2|3|4)px|\bborder-[lr]-(?:1|2|3)\b	gi
surface.pseudo-stripe	P2	default-risk	css	Pseudo-element accent bar signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.pseudo-stripe	0	::(?:before|after)[^{]{0,80}\{[^}]{0,500}((?:width|height)\s*:\s*[1-6]px[^}]{0,400}background(?:-color)?\s*:\s*(?:#[0-9a-f]{3,8}|rgba?\()|background(?:-color)?\s*:\s*(?:#[0-9a-f]{3,8}|rgba?\()[^}]{0,400}(?:width|height)\s*:\s*[1-6]px)	gi
surface.inset-stripe	P2	default-risk	css	Inset edge-shadow stripe signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.inset-stripe	0	box-shadow\s*:\s*inset\s+(?:0\s+[-]?[1-9]px|[-]?[1-9]px\s+0)(?:\s+(?:0|\d+px))?\s+(?:#[0-9a-f]{3,8}|rgba?\([^)]*\)|[a-z]{3,})	gi
surface.gradient-border-image	P2	default-risk	css	Gradient border-image signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.gradient-border-image	0	border-image(?:-source)?\s*:\s*[^;{}]{0,200}linear-gradient\(	gi
surface.hard-stop-band	P2	default-risk	css	Hard-stop gradient band signature	review	Confirm the stripe carries state or brand meaning before replacing.	Static source signatures require context before remediation.		review	surface.hard-stop-band	0	linear-gradient\([^;{}]*\b(?:2|3|4|5|6|7|8)px\b[^;{}]*\b(?:2|3|4|5|6|7|8)px\b	gi
structure.card-in-card	P2	default-risk	markup	Nearby nested/repeated card class signature	review	Inspect DOM nesting and preserve semantic groups.	Static source signatures require context before remediation.		review	structure.card-in-card	0	class(?:Name)?\s*=\s*["'`][^"'`]*\bcard\b[^"'`]*["'`][\s\S]{0,500}class(?:Name)?\s*=\s*["'`][^"'`]*\bcard\b	gi
quality.fake-chrome	P2	default-risk	text	Fake device/application chrome naming signature	review	Preserve chrome that frames a real product asset or communicates context.	Static source signatures require context before remediation.		review	quality.fake-chrome	0	(?:fake|mock)[-_ ]?(?:browser|phone|terminal|ide)|(?:browser|phone|terminal|ide)[-_ ]?chrome	gi
copy.placeholder-person	P1	default-risk	text	Obvious placeholder person or copy	remove	Remove only when it is not a documented fixture or functional test value.	Static source signatures require context before remediation.		autofix-safe	copy.placeholder-person	0	\b(?:John Doe|Jane Doe|Lorem Ipsum)\b	gi
copy.placeholder-brand	P1	default-risk	text	Common placeholder brand signature	review	Confirm it is not the actual product or an intentional fixture.	Static source signatures require context before remediation.		review	copy.placeholder-brand	0	\b(?:Acme|SmartFlow|Nexus AI)\b	gi
copy.cliche	P3	context-dependent	text	Generic marketing cliché	review	Review against product voice; do not rewrite sourced copy automatically.	Static source signatures require context before remediation.		review	copy.cliche	0	\b(?:Elevate|Seamless(?:ly)?|Next-gen|Next[- ]generation|Unleash|Game-changer|Supercharge|Cutting[- ]edge|Revolutionary|AI[- ]powered|Effortless(?:ly)?)\b	gi
copy.unsupported-metric	P1	default-risk	text	Metric-like marketing claim	review	Require local provenance; never invent a replacement metric.	Static source signatures require context before remediation.		review	copy.unsupported-metric	0	\b(?:\d{2,}(?:\.\d+)?%|\d+x)\s+(?:faster|better|growth|uptime|increase|improvement|more)\b	gi
motion.scale-everywhere	P2	default-risk	text	Generic hover-scale utility	review	Confirm scaling communicates hierarchy or interaction.	Static source signatures require context before remediation.		review	motion.scale-everywhere	0	\bhover:(?:scale-(?:105|110)|transform[^\s"'`]*)\b	gi
structure.three-equal-cards	P1	context-dependent	text	Three equal grid tracks	review	Preserve real three-peer comparisons and user-required cardinality.	Static source signatures require context before remediation.	pricing or comparison data	review	structure.three-equal-cards	0	\b(?:grid-cols-3|repeat\(\s*3\s*,\s*(?:1fr|minmax\(0,\s*1fr\))\s*\))	gi
surface.decorative-orb	P2	default-risk	text	Decorative orb/blob naming signature	review	Remove only when source/DOM confirms no semantic, brand, state, or interaction role.	Static source signatures require context before remediation.		review	surface.decorative-orb	0	(?:decorative|floating|gradient)[-_ ]?(?:orb|blob)|\b(?:orb|blob)[-_ ]?(?:decoration|glow)\b	gi
surface.status-dot	P3	default-risk	text	Status/decorative dot naming signature	review	Confirm whether the dot communicates a real state.	Static source signatures require context before remediation.	recording, live, sync, unread state	review	surface.status-dot	0	(?:decorative|pulse|status)[-_ ]?dot	gi
surface.version-label	P3	default-risk	text	Version-label signature	review	Preserve real release/version information.	Static source signatures require context before remediation.		review	surface.version-label	0	(?:version|release)[-_ ]?(?:badge|pill|label)|\bv\d+(?:\.\d+)+\b	gi
quality.missing-alt	P1	universal	markup	Image element without an alt attribute	review	Determine whether the image is informative or decorative before adding alt.	Static source signatures require context before remediation.		review	quality.missing-alt	0	<img\b(?![^>]*\balt\s*=)[^>]*>	gi
quality.focus-suppressed	P1	universal	css	Focus outline suppression signature	review	Confirm an equally visible focus-visible replacement exists.	Static source signatures require context before remediation.		review	quality.focus-suppressed	0	(?:outline\s*:\s*(?:none|0)|\bfocus:outline-none\b)	gi
structure.repeated-eyebrow	P3	review-only	markup	Repeated eyebrow/kicker source signature	review	Keep labels that carry real hierarchy or sequence; otherwise let headings carry the weight.	Static source signatures require context before remediation.		review	repeated-section-scaffold	0	(?:class(?:Name)?\s*=\s*["'`][^"'`]*(?:eyebrow|kicker)[^"'`]*["'`])	gi
structure.numbered-section-label	P3	context-dependent	markup	Numbered section-label source signature	review	Preserve numbers when users need the sequence; otherwise avoid decorative numbering.	Static source signatures require context before remediation.		review	repeated-section-scaffold	0	(?:class(?:Name)?\s*=\s*["'`][^"'`]*(?:section-number|step-number)[^"'`]*["'`][^>]*>\s*0?[1-9]\b)|\b0[1-9]\s*<\/[^>]+>\s*<h[2-6]	gi
structure.identical-icon-card-cluster	P2	context-dependent	markup	Three nearby feature-card and icon-tile signatures	review	Preserve actual peer data; otherwise review a task-ordered alternative.	Static source signatures require context before remediation.		review	structure.identical-icon-card-cluster	0	(?=(?:[\s\S]*feature-card){3})(?=(?:[\s\S]*icon-tile){3})[\s\S]*	gi
surface.radial-glow	P3	review-only	css	Radial glow-like CSS signature	review	Preserve purposeful lighting or brand material; remove unsupported decorative glow.	Static source signatures require context before remediation.		review	surface.radial-glow	0	radial-gradient\([^;}]*(?:transparent|rgba?\()	gi
surface.grid-background	P3	review-only	css	Repeated linear-gradient grid-background signature	review	Preserve a real map, canvas, blueprint, or measuring surface; otherwise use a purposeful surface.	Static source signatures require context before remediation.		review	surface.grid-background	0	(?:linear-gradient\([^;}]*){2}[\s\S]{0,160}background-size	gi
surface.border-plus-wide-shadow	P3	context-dependent	css	Border plus wide soft-shadow declaration cluster	review	Keep a documented elevation system; otherwise choose the boundary that carries grouping.	Static source signatures require context before remediation.		review	surface.border-plus-wide-shadow	0	border\s*:[^;}]+;[\s\S]{0,200}box-shadow\s*:\s*0\s+(?:1[6-9]|[2-9]\d)px	gi
type.decorative-monospace	P3	default-risk	text	Monospace used with decorative technical-kicker language	review	Reserve monospace for code, IDs, logs, measurements, or real system state.	Static source signatures require context before remediation.		review	type.decorative-monospace	0	(?:font-mono|font-family\s*:\s*[^;}]*monospace)[\s\S]{0,160}(?:kicker|future|platform|work)	gi
motion.pulse-without-state	P2	default-risk	css	Pulse animation signature	review	Preserve real recording, sync, notification, or live state; otherwise use static hierarchy.	Static source signatures require context before remediation.	real state label	review	motion.pulse-without-state	0	animation\s*:\s*[^;}]*pulse|@keyframes\s+pulse	gi
motion.missing-reduced-motion	P1	universal	motion-context	Motion without a project reduced-motion path	review	Check project-wide reduced-motion handling before adding a scoped fallback.	Static source signatures require context before remediation.		review	motion-reduced-preference	0
quality.heading-skip	P2	universal	markup	Heading level skips from h1 to h3	review	Use a semantic heading hierarchy; confirm component composition before changing levels.	Static source signatures require context before remediation.		review	quality.heading-skip	0	<h1\b[\s\S]{0,500}<h3\b	gi
quality.zoom-blocked	P1	universal	markup	Viewport meta that blocks zoom	replace	Remove user-scalable=no and maximum-scale=1 so people can zoom to at least 200%.	Static source signatures require context before remediation.		review	quality.zoom-blocked	0	<meta\b[^>]*(?:user-scalable\s*=\s*(?:no|0)\b|maximum-scale\s*=\s*1(?:\.0+)?\b)[^>]*>	gi
quality.clickable-div	P1	universal	markup	Div or span used as a click target	review	Use a button for an action or an anchor with a real href for navigation; keep keyboard support.	Static source signatures require context before remediation.		review	quality.clickable-div	0	<(?:div|span)\b[^>]*\bon(?:click|Click)\s*=	g
quality.dead-anchor	P2	universal	markup	Anchor whose href is only #	review	Point the link at a real section or page, use a button for an action, or remove the control.	Static source signatures require context before remediation.		review	quality.dead-anchor	0	\bhref\s*=\s*(?:\"#\"|'#'|\{\s*[\"']#[\"']\s*\})	g
quality.media-unsized	P2	universal	markup	Image, video, or iframe without width or height	review	Give the element intrinsic width and height or an aspect-ratio so the layout does not shift.	Static source signatures require context before remediation.		review	quality.media-unsized	0	<(?:img|video|iframe)\b(?![^>]*\b(?:width|height)\s*=)(?![^>]*aspect-ratio)[^>]*>	gi
copy.em-dash	P3	default-risk	text	Em dash in source text	review	Rewrite with a period, comma, colon, or parentheses; keep a voice sample the owner approved.	Static source signatures require context before remediation.	owner voice sample	review	copy.em-dash	0	&(?:mdash|#8212);|—	g
copy.generic-cta	P3	context-dependent	markup	Generic call-to-action label	review	Name the action and its result in the product's words; keep a label the brand guide requires.	Static source signatures require context before remediation.		review	copy.generic-cta	0	>\s*(?:Get started|Learn more|Try (?:it )?now|Explore|Discover)\s*(?:&rarr;|→)?\s*<	gi
structure.viewport-height	P3	context-dependent	css	Full viewport height section	review	Let the section size to its content, or use dvh for a section that must fill the screen.	Static source signatures require context before remediation.		review	structure.viewport-height	0	\b100vh\b|\b(?:min-)?h-screen\b	g
RULES_TABLE
}

# rule_by_id_exists <rule-id> succeeds when the registry declares the rule.
rule_by_id_exists() {
  case "$1" in
    surface.gradient-text|surface.purple-gradient|motion.transition-all|motion.layout-property|\
    surface.thick-side-stripe|surface.thin-side-stripe|surface.pseudo-stripe|surface.inset-stripe|\
    surface.gradient-border-image|surface.hard-stop-band|structure.card-in-card|quality.fake-chrome|copy.placeholder-person|\
    copy.placeholder-brand|copy.cliche|copy.unsupported-metric|motion.scale-everywhere|\
    structure.three-equal-cards|surface.decorative-orb|surface.status-dot|surface.version-label|\
    quality.missing-alt|quality.focus-suppressed|structure.repeated-eyebrow|\
    structure.numbered-section-label|structure.identical-icon-card-cluster|surface.radial-glow|\
    surface.grid-background|surface.border-plus-wide-shadow|type.decorative-monospace|\
    motion.pulse-without-state|motion.missing-reduced-motion|quality.heading-skip|quality.zoom-blocked|quality.clickable-div|\
    quality.dead-anchor|quality.media-unsized|copy.em-dash|copy.generic-cta|structure.viewport-height) return 0 ;;
  esac
  return 1
}

# rule_registry_field <rule-id> <field-number> prints one field of one rule.
rule_registry_field() {
  rule_registry_rows | awk -F '\t' -v id="$1" -v field="$2" '$1 == id { print $field; exit }'
}

# Direct execution keeps the library inert, matching the module contract.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  :
fi

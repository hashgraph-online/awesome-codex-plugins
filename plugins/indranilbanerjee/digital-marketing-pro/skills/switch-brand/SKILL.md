---
name: switch-brand
description: "Switch the active brand profile for multi-client and agency work by running setup.py --switch-brand, after listing configured brands with the active one starred; confirms the new brand's industry, business model, and primary channel so subsequent outputs use its voice and compliance rules. Triggers on \"/digital-marketing-pro:switch-brand\", \"switch to the other client\", \"change brand to Acme\", \"list available brands\", \"what brands do I have set up\". Can present a side-by-side comparison of two brand profiles on request; offers /digital-marketing-pro:brand-setup when the brand isn't found; pairs with /digital-marketing-pro:status to verify the active context."
argument-hint: "[brand-slug]"
---

# Switch Brand

## When to Use
- User says "switch to [brand name]" or "change brand to..."
- User wants to work on a different client/brand
- User asks to list available brands

## Process

### 1. List Available Brands
Run the setup script to show all configured brands:
```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" --list-brands
```

The currently active brand is marked with `*`.

### 2. Switch Active Brand
When the user selects a brand, run:
```bash
python "${CLAUDE_PLUGIN_ROOT}/scripts/setup.py" --switch-brand BRAND_SLUG
```

### 3. Confirm Switch
After switching, confirm:
- Brand name and slug
- Key profile details (industry, business model, primary channel)
- Remind: "All marketing outputs will now use [brand_name]'s voice, compliance rules, and context."

## If Brand Not Found
- Show the list of available brands
- Offer to create a new brand: "Brand not found. Would you like to create a new profile? Use /digital-marketing-pro:brand-setup"

## Multi-Brand Comparison
If the user asks to compare brands, load both profiles and present a side-by-side comparison of key attributes (voice settings, channels, goals).

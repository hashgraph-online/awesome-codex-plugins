# Citation Optimization — Content Restructuring for AI Citation

## Overview

Techniques for restructuring content so AI platforms are more likely to cite it as a source in generated answers.

---

## Citation-Worthy Content Patterns

### 1. Definitive Statements

AI models favor content that makes clear, unambiguous claims backed by evidence.

**Pattern**: "[Subject] is [definitive claim]. According to [source], [supporting data]."

**Example**: "Customer acquisition cost (CAC) for B2B SaaS companies averages $205 for organic channels and $341 for paid channels. According to a 2024 FirstPageSage study, this represents a 15% increase from 2023."

### 2. Data-First Paragraphs

Lead paragraphs with specific numbers, dates, or statistics.

**Weak**: "Email marketing is very effective for businesses."
**Strong**: "Email marketing delivers an average ROI of $36 for every $1 spent (Litmus 2023), making it the highest-ROI digital marketing channel across industries."

### 3. Structured Definitions

AI models frequently pull definitional content for "what is" queries.

**Format**:
```
[Term] is [concise definition in one sentence]. It [expanded explanation].
Key characteristics include: [list of 3-5 defining features].
```

### 4. Comparison Tables

Structured comparisons are high-value citation targets.

```markdown
| Feature | Option A | Option B | Option C |
|---------|----------|----------|----------|
| Price   | $X/mo    | $Y/mo    | $Z/mo    |
| Best for| [use case]| [use case]| [use case]|
```

### 5. Step-by-Step Processes

Numbered processes are frequently cited for "how to" queries.

---

## Content Formatting Rules for LLM Ingestion

1. **Concise paragraphs**: 2-4 sentences max. AI models parse shorter paragraphs more reliably
2. **Entity-rich text**: Include full proper names, specific numbers, and verifiable facts
3. **Clear heading hierarchy**: H1 → H2 → H3 with descriptive headings (not clever/vague)
4. **Front-load key info**: Put the most citation-worthy statement in the first sentence of each section
5. **Avoid hedging language**: "Arguably" and "some experts say" reduce citation likelihood
6. **Include recency signals**: Dates, "as of [year]," version numbers
7. **Use lists and tables**: Structured data formats are easier for AI to parse and cite
8. **Attribute claims**: Link to primary research, not secondary sources

---

## Schema Markup for AI Citation

### FAQ Schema (JSON-LD)

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [{
    "@type": "Question",
    "name": "What is [topic]?",
    "acceptedAnswer": {
      "@type": "Answer",
      "text": "Concise, definitive answer here."
    }
  }]
}
```

### HowTo Schema

```json
{
  "@context": "https://schema.org",
  "@type": "HowTo",
  "name": "How to [achieve outcome]",
  "step": [{
    "@type": "HowToStep",
    "name": "Step name",
    "text": "Step description"
  }]
}
```

### Organization Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Brand Name",
  "description": "One-sentence brand description",
  "url": "https://brand.com",
  "foundingDate": "YYYY",
  "founder": {"@type": "Person", "name": "Founder Name"},
  "sameAs": ["LinkedIn URL", "Twitter URL", "Crunchbase URL"]
}
```

### Article Schema

```json
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "Article title",
  "author": {
    "@type": "Person",
    "name": "Author Name",
    "url": "Author profile URL",
    "jobTitle": "Title"
  },
  "datePublished": "YYYY-MM-DD",
  "dateModified": "YYYY-MM-DD",
  "publisher": {"@type": "Organization", "name": "Brand"}
}
```

---

## Source Authority Building

### Tier 1: Owned Authority
- Publish original research with proprietary data
- Create definitive guides (3,000+ words with unique frameworks)
- Maintain expert author profiles with verifiable credentials
- Keep content updated (dated content loses citation preference)

### Tier 2: Earned Authority
- Get cited in industry publications
- Earn Wikipedia references (do NOT edit Wikipedia directly)
- Build Wikidata entity with proper sourcing
- Secure .edu or .gov backlinks

### Tier 3: Structured Authority
- Implement comprehensive schema markup
- Ensure Knowledge Graph accuracy
- Maintain consistent NAP (Name, Address, Phone) across directories
- Cross-reference brand info across Crunchbase, LinkedIn, About page

---

## Citation Testing Process

1. **Publish optimized content** with all formatting and schema
2. **Wait 2-4 weeks** for indexing and AI model retrieval refresh
3. **Test target queries** across all 5 AI platforms
4. **Document results** with exact AI text and source attribution
5. **Compare to baseline** (pre-optimization audit)
6. **Iterate**: If not cited, analyze what the cited source has that yours doesn't
7. **Re-test** after each significant update

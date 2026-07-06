# Executable spec for the /domain skill — the ubiquitous-language corpus (BC1 Corpus / inner hexagon).
# /domain is the canonical vocabulary root: it curates the load-on-demand corpus of concept
# entries every other skill anchors to. As the language source it consumes nothing (consumes:[]
# is correct — it is the shared kernel others point at, not a consumer); it produces vocabulary.
# Entries promote draft -> canonical only under operator approval (the growth ratchet). (soc-qk4b)

Feature: Domain is the load-on-demand ubiquitous-language corpus
  As the inner hexagon's vocabulary root
  I want the shared language curated as on-demand, status-gated entries
  So that every skill anchors to one canonical register without preloading the whole corpus

  Scenario: vocabulary is loaded on demand, not preloaded
    When an agent needs a term
    Then it reads the specific entry (and references/INDEX.md to find it)
    And it does not preload the entire corpus

  Scenario: entries promote draft to canonical only under the ratchet
    Given a new corpus entry
    Then it starts as status: draft
    And promotion to canonical requires operator approval (not self-promotion)

  Scenario: domain is the language source, consuming nothing
    Then /domain's hexagon consumes no other skill (consumes:[] is correct for the vocabulary root)
    And other skills relate to it as the shared kernel

  Scenario: the index catalogs every entry
    Then references/INDEX.md lists each entry by slug, concept, status, and kind

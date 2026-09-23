# EU/PL Law Tracker

Skill do analizy statusu regulacji UE i powiązanych aktów/projektów w Polsce.

## Struktura

- `SKILL.md` — instrukcja operacyjna.
- `references/` — źródła, wzorce identyfikatorów, wiarygodność, szablony raportu.
- `scripts/` — pomocnicze skrypty CLI do identyfikacji i ekstrakcji danych.

## Szybkie użycie skryptów

```bash
python scripts/eu_law_identify.py --query "CBAM" --aliases references/regulation-aliases.yaml
python scripts/eu_law_parse.py --input-file path/to/act.txt
python scripts/legal_date_extractor.py --input-file path/to/act.txt
python scripts/relation_extractor.py --input-file path/to/act.txt
```

Wyniki skryptów traktuj jako pomocnicze i zawsze waliduj w źródłach urzędowych.


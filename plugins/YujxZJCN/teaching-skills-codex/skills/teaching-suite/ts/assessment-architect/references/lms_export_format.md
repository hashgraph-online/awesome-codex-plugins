# LMS export format

The question-set JSON that `ts/scripts/export_lms.py` consumes to produce LMS-importable
artifacts (GIFT for Moodle, QTI 2.1 for Canvas/Blackboard, a Common Cartridge course
package). When `item_writer_agent` builds an exam or quiz, it emits this JSON alongside
the human-readable Markdown so the instrument can reach the LMS quiz engine without
retyping — closing the gap where assessments shipped as Markdown only.

## Shape

```json
{
  "title": "Midterm",
  "questions": [
    { "type": "multiple_choice", "id": "q1", "prompt": "…", "points": 2,
      "choices": ["A", "B", "C", "D"], "answer": 0 },
    { "type": "multiple_answer", "prompt": "…", "choices": ["A","B","C"], "answer": [0,2] },
    { "type": "true_false", "prompt": "…", "answer": true },
    { "type": "short_answer", "prompt": "…", "answers": ["mitosis", "cell division"] },
    { "type": "essay", "prompt": "…", "points": 10 }
  ]
}
```

| Field | Notes |
|-------|-------|
| `type` | one of `multiple_choice`, `multiple_answer`, `true_false`, `short_answer`, `essay` |
| `id` | optional; auto-assigned `q1, q2, …` if omitted |
| `points` | optional; default 1 |
| `answer` | MC: 0-based index. multiple_answer: list of indices. true_false: bool |
| `answers` | short_answer: list of accepted strings (case-insensitive on most LMS) |

## Export targets

```bash
python3 scripts/export_lms.py questions.json --to gift  -o quiz.txt        # Moodle import
python3 scripts/export_lms.py questions.json --to qti   -o quiz_qti.zip    # QTI 2.1 (Canvas/Bb)
python3 scripts/export_lms.py questions.json --to imscc -o course.imscc --syllabus syllabus.md
```

## Honest scope

Covers the five common item types and the QTI 2.1 / Common Cartridge 1.3 shapes most LMS
accept. Exotic item types (matching, numeric-with-tolerance, cloze) and per-LMS import
quirks may need a manual tweak on import — the export gets you 90% there, not a guaranteed
byte-perfect import. Auto-graded scoring for essay/short-answer still needs human review,
as the suite always insists.

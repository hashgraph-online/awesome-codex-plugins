# Plan: <FEATURE_TITLE>
Source: <SOURCE_PATH>
Created: <ISO_TIMESTAMP>
Status: draft

## Summary

<ONE_PARAGRAPH_SUMMARY_OF_WHAT_THIS_PLAN_IMPLEMENTS_AND_WHY>

## Files (whole-plan)

- Create:
  - <PATH_TO_NEW_FILE_1>
  - <PATH_TO_NEW_FILE_2>
- Modify:
  - <PATH_TO_EXISTING_FILE_1>
  - <PATH_TO_EXISTING_FILE_2>
- Test:
  - <PATH_TO_TEST_FILE_1>
  - <PATH_TO_TEST_FILE_2>

---

## Task 1: <TASK_1_TITLE>

Owner: <AGENT_ROLE>
Estimated: <MINUTES> min

### Files

- Create: <PATHS_OR_NONE>
- Modify: <PATHS_OR_NONE>
- Test: <PATHS_OR_NONE>

### Step 1: Write the failing test

File: `<TEST_FILE_PATH>`

```<LANG>
<COMPLETE_TEST_CODE>
// All imports, describe blocks, and assertions included.
// No placeholders. Runnable as-is.
```

Why: <ONE_SENTENCE_EXPLAINING_WHAT_BEHAVIOR_THIS_TEST_VERIFIES>

### Step 2: Run to confirm failure

Command: `<EXACT_COMMAND>`

Expected output:
```
<EXPECTED_FAILURE_OUTPUT>
// The specific assertion error line that proves the test exercises missing code.
// Example: AssertionError: expected undefined to equal 'value'
```

### Step 3: Implement

Files:
- Create: `<PATH>` / Modify: `<PATH>`

```<LANG>
<COMPLETE_IMPLEMENTATION_CODE>
// All imports, exports, and logic included.
// No placeholders. No "// add error handling". No "...".
```

### Step 4: Run to verify pass

Command: `<EXACT_COMMAND>` (same as Step 2)

Expected output:
```
<EXPECTED_PASS_OUTPUT>
// Example: ✓ Task 1 description (12ms)
// 1 passed
```

### Step 5: Commit

Message:
```
<TYPE>(<SCOPE>): <SUBJECT_IN_IMPERATIVE_MOOD_MAX_72_CHARS>
```

Files staged: <LIST_ONLY_THIS_TASKS_FILES>

---

## Task 2: <TASK_2_TITLE>

Owner: <AGENT_ROLE>
Estimated: <MINUTES> min

### Files

- Create: <PATHS_OR_NONE>
- Modify: <PATHS_OR_NONE>
- Test: <PATHS_OR_NONE>

### Step 1: Write the failing test

File: `<TEST_FILE_PATH>`

```<LANG>
<COMPLETE_TEST_CODE>
```

Why: <ONE_SENTENCE_EXPLAINING_WHAT_BEHAVIOR_THIS_TEST_VERIFIES>

### Step 2: Run to confirm failure

Command: `<EXACT_COMMAND>`

Expected output:
```
<EXPECTED_FAILURE_OUTPUT>
```

### Step 3: Implement

Files:
- Create: `<PATH>` / Modify: `<PATH>`

```<LANG>
<COMPLETE_IMPLEMENTATION_CODE>
```

### Step 4: Run to verify pass

Command: `<EXACT_COMMAND>` (same as Step 2)

Expected output:
```
<EXPECTED_PASS_OUTPUT>
```

### Step 5: Commit

Message:
```
<TYPE>(<SCOPE>): <SUBJECT_IN_IMPERATIVE_MOOD_MAX_72_CHARS>
```

Files staged: <LIST_ONLY_THIS_TASKS_FILES>

---

<!-- Add Task N sections following the same structure as Task 1 and Task 2 above. -->
<!-- Every task must have exactly 5 steps in the order: test → fail-run → implement → pass-run → commit. -->
<!-- No task may share a file path with another task. -->

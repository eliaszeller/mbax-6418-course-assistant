# Bug Report: Missing-information fallback raises a validation error

## Summary

When the model returned an invalid or unsupported citation, the course assistant attempted to return its safe missing-information response. That fallback response was then rejected by the `Answer` model validator, causing an exception instead of showing the student a grounded “not found” message.

## Environment

- Application: MBAX 6418 Course Assistant
- Component: `CourseAssistant.answer()` and `Answer.require_sources_for_claims()`
- Language: Python
- Validation library: Pydantic

## Steps to reproduce

1. Create a `CourseAssistant` with at least one valid course chunk.
2. Use a test client whose `complete_json()` response contains an answer with an unknown source ID, for example:

   ```python
   {"answer": "Invented", "sources": [{"source_id": "missing"}]}
   ```

3. Ask a question that is not supported by the indexed course material, such as:

   ```text
   Who won the 2034 World Cup?
   ```

4. The unknown citation causes structured-answer validation to fail.
5. Observe what happens when `CourseAssistant.answer()` constructs its fallback response with an empty source list.

## Expected behavior

The application should catch the invalid model response and return a safe result without citations:

```text
A verifiable answer was not found in the selected course materials.
```

The interface should remain usable and should not invent an answer or citation.

## Actual behavior before the fix

The fallback text was:

```text
The course materials did not provide a verifiable answer.
```

The `Answer` validator allowed an empty source list only when the answer contained the exact phrase `not found`. Because the fallback did not contain that phrase, Pydantic raised a second `ValidationError` while handling the original validation failure. The exception escaped instead of returning the safe response.

## Root cause

The error-handling path and the model validator used inconsistent rules for identifying a missing-information answer. The validator checked for the phrase `not found`, while the fallback used different wording.

## Fix

The fallback was changed to:

```text
A verifiable answer was not found in the selected course materials.
```

This satisfies the validator and clearly communicates that the selected evidence is insufficient.

## Regression test

`tests/test_core.py::CoreTests.test_missing_information_returns_grounded_fallback` supplies an invalid source ID and verifies that:

- no exception is raised;
- the returned source list is empty; and
- the response contains `not found`.

Run the test suite with:

```bash
python -m unittest discover -s tests -v
```

## Status

Fixed and covered by an automated regression test.

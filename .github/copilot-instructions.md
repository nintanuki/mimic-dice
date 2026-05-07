# Copilot Instructions for Arcade Cabinet

## Before making any change
1. Read `docs/CHANGELOG.md` to understand the current state of the codebase.
2. Follow every rule under **Refactoring Rules**.
3. Questions about why code was written a certain way are requests for explanation, not requests for code changes. Do not modify code unless the user explicitly asks for a change.

## After making any change
- Append an entry to `docs/CHANGELOG.md` following the exact format specified in that file (ISO 8601 timestamp with timezone, file path, line numbers at time of edit, before/after code, why, and editor name including the AI model used).

## Refactoring rules (enforced always)
- All code must be PEP-8 compliant.
- Less code is better; clean and readable is best.
- Keep middlemen minimal: if A calls B and B only calls C, have A call C directly.
- Keep code clean of dead imports, unused variables/functions, and legacy code.
- `GameManager` must be light — offload responsibilities to other classes.
- Classes should communicate through `GameManager` where possible.
- New class and function names must clearly describe their purpose.
- All constants go in `settings.py`. No magic numbers.
- All classes and functions must have a docstring with a summary, and Args/Returns if applicable.
- Do not change function or variable names unless their role has completely changed.
- Keep functions grouped by role. `update` and `run` functions go last and should only call other functions.
- Do not remove docstrings from any functions, only update them.
- Do not remove comments unless they are no longer accurate (in which case try to update them instead). Comments must explain *why*, not just what.
- Do not leave comments noting that a change was made, unless fixing a non-obvious bug or explaining unconventional code.

## Display text
- ALL text displayed to the user in the UI must be ALL CAPS.

## Testing checklist (run mentally after major changes)
- Game still loads
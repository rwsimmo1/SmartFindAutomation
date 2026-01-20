Purpose
- Provide contextual instructions for code generation and suggestions tailored to this repository.
- Keep assistant outputs safe (no secrets), consistent with project conventions, and runnable.

Repo overview
- Project: SmartFindAutomation
- Language: Python 3.12
- Frameworks/libraries: Playwright (sync API), python-dotenv, keyring
- Main files:
  - `AutomateSmartFind.py` — orchestration script (Playwright steps, CLI args)
  - `SmartFindScript.py` — helper functions, selectors, credential retrieval, utilities

How to run
- From repo root (PowerShell):
  cd d:\development\SmartFind\Playwright
  python .\AutomateSmartFind.py "MM/DD/YYYY" "MM/DD/YYYY"

Credentials & secrets
- Do NOT hard-code secrets in code or output them.
- Passwords come from Windows Credential Manager via `keyring.get_password("SmartFind", USERNAME)`.
- USERNAME is read from `.env` via `SMARTFIND_USERNAME`.
- Never propose storing secrets in source control.

Coding conventions / expectations
- Use the Playwright sync API (from `playwright.sync_api`).
- Prefer `page.locator(selector)` and explicit waits like `page.wait_for_selector(...)` before interacting.
- Use descriptive constant names for selectors (already present in `SmartFindScript.py`).
- Minimize UI brittle selectors — prefer IDs when stable; otherwise use attribute selectors or text selectors.
- Keep logging via the existing `logging` setup; avoid printing secrets.
- Use defensive checks for optional CLI args (function `read_dates_from_command_line()` returns `(None, None)` if not provided).

Behavioral constraints for suggestions
- Do not change credential retrieval logic unless explicitly requested.
- Avoid adding new runtime dependencies unless justified and agreed.
- When modifying files, prefer minimal, focused edits; preserve original style and formatting.
- Add tests for non-trivial logic changes (small unit tests are preferred).
- When adding new selectors or UI actions, include a fallback or a timeout handling recommendation.

Useful prompts for generating code in this repo
- "Add a function to click the 'Date Range' radio option using a robust selector, scrolling into view if needed, without forcing clicks."
- "Add a unit test for rank_jobs() covering high, mid, low classification and location scoring."
- "Refactor read_dates_from_command_line to accept named flags --start and --end and keep backwards compatibility."
- "Create a launch.json debug configuration for VS Code that runs AutomateSmartFind.py with args."

Edge-cases & checks to include
- Browser autofill overwriting inputs — use clear() then fill(), optionally set input attributes to avoid autocomplete.
- Elements may be outside the viewport — prefer clicking the visible label, or use locator.scroll_into_view_if_needed() before click.
- Ensure `read_dates_from_command_line()` input validation: provide helpful error messages for incorrect formats.
- If Playwright throws timeouts, prefer increasing explicit wait or using `locator.wait_for()` with reasoned timeout.

Commit / PR guidance
- Prefer small focused commits with a short message.
- Don’t commit `.env` or any credentials to the repo.
- Add tests when behavioral changes are introduced.
- Annotate changes that affect selectors with the target page snippet or screenshot if possible.

Contact & context for assistant
- If uncertain about UI selectors, ask for the page HTML snippet or a screenshot.
- If a change could affect credentials or secret handling, request explicit confirmation.

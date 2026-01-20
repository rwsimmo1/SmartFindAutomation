# SmartFindAutomation

Automate the SmartFindExpress website.

## Overview

This repository contains a small Playwright-based automation that logs into SmartFindExpress and interacts with the Available / Active jobs workflow.

Main files
- `AutomateSmartFind.py` — orchestration script (Playwright steps, program entrypoint)
- `SmartFindScript.py` — helpers, selectors, credential retrieval, and page-interaction helpers

## Prerequisites

- Windows (the project expects Windows Credential Manager for securely storing passwords)
- Python 3.11+ (this repo uses Python 3.12 in development)
- Install dependencies:

```powershell
pip install -r requirements.txt
# or (if no requirements file)
pip install playwright python-dotenv keyring
playwright install
```

## Configuration

- Create a `.env` file in the `Playwright` folder (do NOT commit it). At minimum set:

```
SMARTFIND_WEBSITE_URL=https://your.smartfind.url
SMARTFIND_USERNAME=your.username
```

- Store the password in Windows Credential Manager as a Generic Credential with the target name `SmartFind` and the username matching `SMARTFIND_USERNAME`. The code uses `keyring.get_password("SmartFind", USERNAME)` to retrieve it.

## Running

From PowerShell in the `Playwright` folder run:

```powershell
cd d:\development\SmartFind\Playwright
python .\AutomateSmartFind.py "MM/DD/YYYY" "MM/DD/YYYY"
```

Both date arguments are optional. The script reads them via `read_dates_from_command_line()` and will continue without date filters if none are provided.

## Debugging in VS Code

- Create a `.vscode/launch.json` and add a configuration that passes args to `AutomateSmartFind.py`. Example:

```json
{
	"version": "0.2.0",
	"configurations": [
		{
			"name": "Python: AutomateSmartFind (with dates)",
			"type": "python",
			"request": "launch",
			"program": "${workspaceFolder}/Playwright/AutomateSmartFind.py",
			"console": "integratedTerminal",
			"cwd": "${workspaceFolder}/Playwright",
			"args": ["10/29/2025", "11/29/2025"]
		}
	]
}
```

## Notes & conventions

- Use the Playwright sync API (`playwright.sync_api`) and prefer `page.locator(...)` with explicit waits (`page.wait_for_selector(...)`) before interacting.
- Selectors live in `SmartFindScript.py` as constants — prefer ID selectors where available and add fallbacks when pages may render differently.
- Do not hard-code secrets. Username goes in `.env`; passwords are read from Windows Credential Manager via `keyring`.
- There is a `.github/copilot-instructions.md` with repository-specific guidance for AI assistants. Keep that file free of secrets.

## Troubleshooting

- If a click fails saying an element is "outside the viewport", try clicking a visible label, calling `locator.scroll_into_view_if_needed()` first, or using `force=True` as a last resort.
- If keyring returns `None` for the password, verify the Generic Credential exists in Windows Credential Manager with target `SmartFind` and the correct username.

## License / Contributing

Follow the project's standard contribution practices. Don’t commit `.env` or any credentials.

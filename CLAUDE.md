# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

This repository is a single-file Python hook with no package manifest, build step, third-party dependencies, or committed test suite.

- Smoke-test the hook entry point:
  ```bash
  python popup_hook.py test
  ```
- Check syntax/bytecode compilation:
  ```bash
  python -m py_compile popup_hook.py
  ```
- Verify `tkinter` is available in the active Python installation:
  ```bash
  python - <<'PY'
  import tkinter
  print('tkinter ok')
  PY
  ```
- Manually exercise the permission hook with sample Claude Code input:
  ```bash
  python popup_hook.py permission <<'JSON'
  {"hook_event_name":"PermissionRequest","tool_name":"Bash","tool_input":{"command":"pwd"},"permission_suggestions":[]}
  JSON
  ```
- Manually exercise the idle notification hook:
  ```bash
  python popup_hook.py notification <<'JSON'
  {"notification_type":"idle_prompt","message":"Claude Code is idle"}
  JSON
  ```

## Repository purpose

This repo centrally stores personal Claude Code hooks. The current hook, `popup_hook.py`, turns Claude Code permission requests and idle notifications into Windows desktop popups so the user can respond without focusing the terminal.

The README is the source of user-facing installation instructions, including the global `settings.json` hook configuration. Keep its examples aligned with any changes to hook modes, expected arguments, or behavior.

## Runtime architecture

`popup_hook.py` is intentionally self-contained and uses only the Python standard library:

- `main()` selects a mode from `argv[1]`: `permission`, `notification`, `test`, or a fallback no-op JSON response.
- `read_payload()` reads Claude Code hook JSON from stdin. Malformed or empty input is converted to a non-fatal payload instead of raising.
- `permission_dialog()` builds the custom `tkinter` approval window for `PermissionRequest`. It previews `tool_name`, `tool_input`, and the first available `permission_suggestions` entry.
- `emit_permission_result()` converts the dialog choice into Claude Code hook output:
  - `Yes` emits an allow decision for this tool call.
  - `Yes, don't ask again` emits allow and, when present, includes the first suggestion in `updatedPermissions`.
  - `No` emits a deny decision with `interrupt: true`.
  - `Terminal` / close / Escape emits only `suppressOutput`, causing Claude Code to fall back to its normal terminal permission prompt.
- `notification_popup()` handles `Notification` events, especially `idle_prompt`, using `tkinter.messagebox`.

All hook execution is wrapped so unexpected exceptions return a JSON `systemMessage` and exit with status 0. Preserve this fail-open behavior: hook bugs should not break the Claude Code session.

## Platform assumptions

The hook is designed for Windows desktop usage with Python 3.8+ and bundled `tkinter`. UI labels and README documentation are primarily Chinese, with some Claude Code button labels kept in English to match the permission UX.

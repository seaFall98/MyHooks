#!/usr/bin/env python3
"""Claude Code popup hooks for Windows.

Provides interactive permission dialogs and idle notifications using tkinter.
No third-party dependencies are required.
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext


MAX_PREVIEW_CHARS = 6000


def read_payload() -> dict:
    try:
        raw = sys.stdin.read()
        if not raw.strip():
            return {}
        return json.loads(raw)
    except Exception as exc:  # Keep hooks non-fatal on malformed input.
        return {"_parse_error": str(exc)}


def clip(value: str, limit: int = MAX_PREVIEW_CHARS) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + f"\n\n... (truncated, {len(value) - limit} more chars)"


def pretty(value) -> str:
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, ensure_ascii=False, indent=2)
    except Exception:
        return str(value)


def center(win: tk.Tk, width: int, height: int) -> None:
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = max(0, (sw - width) // 2)
    y = max(0, (sh - height) // 2)
    win.geometry(f"{width}x{height}+{x}+{y}")


def make_root(title: str, width: int, height: int) -> tk.Tk:
    root = tk.Tk()
    root.title(title)
    root.attributes("-topmost", True)
    root.resizable(True, True)
    center(root, width, height)
    try:
        root.after(250, lambda: root.attributes("-topmost", False))
        root.bell()
    except Exception:
        pass
    return root


def permission_dialog(payload: dict) -> str:
    """Return allow, deny, or defer."""
    tool_name = payload.get("tool_name", "Unknown tool")
    tool_input = payload.get("tool_input", {})
    suggestions = payload.get("permission_suggestions") or []

    root = make_root("Claude Code 权限申请", 760, 560)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(2, weight=1)

    title = tk.Label(
        root,
        text=f"Claude Code 请求使用：{tool_name}",
        font=("Microsoft YaHei UI", 14, "bold"),
        anchor="w",
        padx=16,
        pady=12,
    )
    title.grid(row=0, column=0, sticky="ew")

    hint = tk.Label(
        root,
        text="请选择允许、拒绝，或返回终端使用 Claude Code 原始确认界面。",
        anchor="w",
        padx=16,
        pady=4,
        fg="#555555",
    )
    hint.grid(row=1, column=0, sticky="ew")

    preview = scrolledtext.ScrolledText(root, wrap=tk.WORD, padx=10, pady=10)
    preview.insert(tk.END, "Tool input:\n")
    preview.insert(tk.END, clip(pretty(tool_input)))
    if suggestions:
        preview.insert(tk.END, "\n\nPermission suggestions:\n")
        preview.insert(tk.END, clip(pretty(suggestions)))
    preview.configure(state="disabled")
    preview.grid(row=2, column=0, sticky="nsew", padx=16, pady=10)

    result = {"value": "defer"}

    def choose(value: str) -> None:
        result["value"] = value
        root.destroy()

    buttons = tk.Frame(root, padx=16, pady=14)
    buttons.grid(row=3, column=0, sticky="ew")
    buttons.columnconfigure((0, 1, 2), weight=1)

    tk.Button(buttons, text="允许本次", command=lambda: choose("allow"), height=2).grid(
        row=0, column=0, sticky="ew", padx=(0, 8)
    )
    tk.Button(buttons, text="拒绝", command=lambda: choose("deny"), height=2).grid(
        row=0, column=1, sticky="ew", padx=8
    )
    tk.Button(buttons, text="回到终端选择", command=lambda: choose("defer"), height=2).grid(
        row=0, column=2, sticky="ew", padx=(8, 0)
    )

    root.protocol("WM_DELETE_WINDOW", lambda: choose("defer"))
    root.bind("<Escape>", lambda _event: choose("defer"))
    root.bind("<Return>", lambda _event: choose("allow"))
    root.mainloop()
    return result["value"]


def notification_popup(payload: dict) -> None:
    notification_type = payload.get("notification_type") or payload.get("matcher") or "notification"
    title = payload.get("title") or "Claude Code 通知"
    message = payload.get("message") or "Claude Code 正在等待你的操作。"

    root = tk.Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    try:
        root.bell()
        if notification_type == "idle_prompt":
            messagebox.showinfo("Claude Code 已空闲", message, parent=root)
        elif notification_type == "permission_prompt":
            messagebox.showinfo("Claude Code 权限申请", message, parent=root)
        else:
            messagebox.showinfo(title, message, parent=root)
    finally:
        root.destroy()


def emit_permission_decision(decision: str) -> None:
    if decision in {"allow", "deny"}:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PermissionRequest",
                        "decision": {"behavior": decision},
                    },
                    "suppressOutput": True,
                },
                ensure_ascii=False,
            )
        )
    else:
        # No decision: let Claude Code show its normal terminal permission prompt.
        print(json.dumps({"suppressOutput": True}, ensure_ascii=False))


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "notification"
    payload = read_payload()

    try:
        if mode == "permission":
            decision = permission_dialog(payload)
            emit_permission_decision(decision)
        elif mode == "notification":
            notification_popup(payload)
            print(json.dumps({"suppressOutput": True}, ensure_ascii=False))
        elif mode == "test":
            print("popup_hook.py ok")
        else:
            print(json.dumps({"suppressOutput": True}, ensure_ascii=False))
    except Exception as exc:
        # Hooks should not break Claude Code. Surface the issue as context if needed.
        print(
            json.dumps(
                {
                    "systemMessage": "Claude Code popup hook failed: " + str(exc),
                    "suppressOutput": False,
                },
                ensure_ascii=False,
            )
        )
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

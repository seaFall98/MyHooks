#!/usr/bin/env python3
"""Claude Code popup hooks for Windows.

Provides interactive permission dialogs and idle notifications using tkinter.
No third-party dependencies are required.
"""

from __future__ import annotations

import json
import sys
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk


MAX_PREVIEW_CHARS = 6000
FONT_FAMILY = "Microsoft YaHei UI"
COLORS = {
    "bg": "#f6f8fb",
    "card": "#ffffff",
    "border": "#d8dee9",
    "text": "#1f2937",
    "muted": "#64748b",
    "primary": "#2563eb",
    "primary_hover": "#1d4ed8",
    "success": "#16a34a",
    "success_hover": "#15803d",
    "danger": "#dc2626",
    "danger_hover": "#b91c1c",
    "secondary": "#e5e7eb",
    "secondary_hover": "#d1d5db",
    "code_bg": "#0f172a",
    "code_fg": "#e5e7eb",
}


def read_stdin_text() -> str:
    """Read hook input as UTF-8 regardless of the Windows console code page."""
    try:
        return sys.stdin.buffer.read().decode("utf-8-sig")
    except Exception:
        return sys.stdin.read()


def write_stdout_text(text: str) -> None:
    """Write hook output as UTF-8 so Chinese JSON content is not mojibake."""
    data = (text + "\n").encode("utf-8")
    try:
        sys.stdout.buffer.write(data)
        sys.stdout.buffer.flush()
    except Exception:
        sys.stdout.write(text + "\n")
        sys.stdout.flush()


def emit_json(value: dict) -> None:
    write_stdout_text(json.dumps(value, ensure_ascii=False))


def read_payload() -> dict:
    try:
        raw = read_stdin_text()
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
    root.configure(bg=COLORS["bg"])
    root.attributes("-topmost", True)
    root.resizable(True, True)
    center(root, width, height)
    try:
        root.after(300, lambda: root.attributes("-topmost", False))
        root.bell()
    except Exception:
        pass
    return root


def style_ttk(root: tk.Tk) -> None:
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass
    style.configure("TFrame", background=COLORS["bg"])
    style.configure("Card.TFrame", background=COLORS["card"], relief="flat")
    style.configure("Muted.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=(FONT_FAMILY, 9))
    style.configure("Title.TLabel", background=COLORS["card"], foreground=COLORS["text"], font=(FONT_FAMILY, 16, "bold"))
    style.configure("Subtitle.TLabel", background=COLORS["card"], foreground=COLORS["muted"], font=(FONT_FAMILY, 10))
    style.configure("Tool.TLabel", background=COLORS["primary"], foreground="#ffffff", font=(FONT_FAMILY, 10, "bold"), padding=(10, 4))


def button(parent, text: str, command, bg: str, hover_bg: str, fg: str = "#ffffff") -> tk.Button:
    btn = tk.Button(
        parent,
        text=text,
        command=command,
        bg=bg,
        fg=fg,
        activebackground=hover_bg,
        activeforeground=fg,
        relief="flat",
        bd=0,
        padx=14,
        pady=10,
        cursor="hand2",
        font=(FONT_FAMILY, 10, "bold"),
    )
    btn.bind("<Enter>", lambda _event: btn.configure(bg=hover_bg))
    btn.bind("<Leave>", lambda _event: btn.configure(bg=bg))
    return btn


def first_permission_suggestion(payload: dict):
    suggestions = payload.get("permission_suggestions") or []
    if isinstance(suggestions, list) and suggestions:
        return suggestions[0]
    return None


def suggestion_summary(suggestion) -> str:
    if not suggestion:
        return "没有收到 Claude Code 的权限规则建议；此按钮将只允许本次。"
    if isinstance(suggestion, dict):
        destination = suggestion.get("destination", "unknown")
        behavior = suggestion.get("behavior", "allow")
        rules = suggestion.get("rules") or []
        if rules:
            rendered_rules = ", ".join(
                f"{rule.get('toolName', '*')}({rule.get('ruleContent', '')})" if isinstance(rule, dict) else str(rule)
                for rule in rules[:3]
            )
            if len(rules) > 3:
                rendered_rules += f", +{len(rules) - 3} more"
            return f"将添加 {behavior} 规则到 {destination}: {rendered_rules}"
        return f"将应用权限更新到 {destination}: {suggestion.get('type', 'permission update')}"
    return pretty(suggestion)


def permission_dialog(payload: dict) -> dict:
    """Return a result with action: allow, allow_remember, deny, or defer."""
    tool_name = payload.get("tool_name", "Unknown tool")
    tool_input = payload.get("tool_input", {})
    suggestion = first_permission_suggestion(payload)

    root = make_root("Claude Code 权限申请", 860, 640)
    style_ttk(root)
    root.columnconfigure(0, weight=1)
    root.rowconfigure(0, weight=1)

    container = tk.Frame(root, bg=COLORS["bg"], padx=18, pady=18)
    container.grid(row=0, column=0, sticky="nsew")
    container.columnconfigure(0, weight=1)
    container.rowconfigure(0, weight=1)

    card = tk.Frame(container, bg=COLORS["card"], highlightthickness=1, highlightbackground=COLORS["border"])
    card.grid(row=0, column=0, sticky="nsew")
    card.columnconfigure(0, weight=1)
    card.rowconfigure(3, weight=1)

    header = tk.Frame(card, bg=COLORS["card"], padx=22, pady=18)
    header.grid(row=0, column=0, sticky="ew")
    header.columnconfigure(1, weight=1)

    icon = tk.Label(
        header,
        text="⚡",
        bg=COLORS["primary"],
        fg="#ffffff",
        font=(FONT_FAMILY, 18, "bold"),
        width=3,
        height=1,
    )
    icon.grid(row=0, column=0, rowspan=2, sticky="nw", padx=(0, 14))

    title = tk.Label(
        header,
        text="Claude Code 请求权限",
        bg=COLORS["card"],
        fg=COLORS["text"],
        font=(FONT_FAMILY, 17, "bold"),
        anchor="w",
    )
    title.grid(row=0, column=1, sticky="ew")

    subtitle = tk.Label(
        header,
        text="请确认是否允许下面的工具调用。Enter 允许本次，Esc 返回终端。",
        bg=COLORS["card"],
        fg=COLORS["muted"],
        font=(FONT_FAMILY, 10),
        anchor="w",
    )
    subtitle.grid(row=1, column=1, sticky="ew", pady=(4, 0))

    tool_row = tk.Frame(card, bg=COLORS["card"], padx=22)
    tool_row.grid(row=1, column=0, sticky="ew")
    tk.Label(
        tool_row,
        text="工具",
        bg=COLORS["card"],
        fg=COLORS["muted"],
        font=(FONT_FAMILY, 9, "bold"),
    ).pack(side=tk.LEFT)
    tk.Label(
        tool_row,
        text=str(tool_name),
        bg=COLORS["primary"],
        fg="#ffffff",
        font=(FONT_FAMILY, 10, "bold"),
        padx=10,
        pady=4,
    ).pack(side=tk.LEFT, padx=(10, 0))

    remember_text = suggestion_summary(suggestion)
    remember_row = tk.Frame(card, bg="#eff6ff", padx=14, pady=10, highlightthickness=1, highlightbackground="#bfdbfe")
    remember_row.grid(row=2, column=0, sticky="ew", padx=22, pady=(14, 8))
    tk.Label(
        remember_row,
        text="Don't ask again",
        bg="#eff6ff",
        fg=COLORS["primary"],
        font=(FONT_FAMILY, 9, "bold"),
    ).pack(anchor="w")
    tk.Label(
        remember_row,
        text=remember_text,
        bg="#eff6ff",
        fg=COLORS["text"],
        font=(FONT_FAMILY, 9),
        wraplength=760,
        justify="left",
    ).pack(anchor="w", pady=(3, 0))

    preview_frame = tk.Frame(card, bg=COLORS["card"], padx=22, pady=8)
    preview_frame.grid(row=3, column=0, sticky="nsew")
    preview_frame.columnconfigure(0, weight=1)
    preview_frame.rowconfigure(1, weight=1)

    tk.Label(
        preview_frame,
        text="Tool input preview",
        bg=COLORS["card"],
        fg=COLORS["muted"],
        font=(FONT_FAMILY, 9, "bold"),
        anchor="w",
    ).grid(row=0, column=0, sticky="ew", pady=(0, 6))

    preview = scrolledtext.ScrolledText(
        preview_frame,
        wrap=tk.WORD,
        padx=12,
        pady=12,
        relief="flat",
        bd=0,
        bg=COLORS["code_bg"],
        fg=COLORS["code_fg"],
        insertbackground=COLORS["code_fg"],
        font=("Consolas", 10),
    )
    preview.insert(tk.END, clip(pretty(tool_input)))
    preview.configure(state="disabled")
    preview.grid(row=1, column=0, sticky="nsew")

    result = {"action": "defer", "suggestion": suggestion}

    def choose(action: str) -> None:
        result["action"] = action
        root.destroy()

    footer = tk.Frame(card, bg=COLORS["card"], padx=22, pady=18)
    footer.grid(row=4, column=0, sticky="ew")
    footer.columnconfigure((0, 1, 2, 3), weight=1)

    button(footer, "Yes", lambda: choose("allow"), COLORS["success"], COLORS["success_hover"]).grid(
        row=0, column=0, sticky="ew", padx=(0, 8)
    )
    button(
        footer,
        "Yes, don't ask again",
        lambda: choose("allow_remember"),
        COLORS["primary"],
        COLORS["primary_hover"],
    ).grid(row=0, column=1, sticky="ew", padx=8)
    button(footer, "No", lambda: choose("deny"), COLORS["danger"], COLORS["danger_hover"]).grid(
        row=0, column=2, sticky="ew", padx=8
    )
    button(
        footer,
        "Terminal",
        lambda: choose("defer"),
        COLORS["secondary"],
        COLORS["secondary_hover"],
        fg=COLORS["text"],
    ).grid(row=0, column=3, sticky="ew", padx=(8, 0))

    root.protocol("WM_DELETE_WINDOW", lambda: choose("defer"))
    root.bind("<Escape>", lambda _event: choose("defer"))
    root.bind("<Return>", lambda _event: choose("allow"))
    root.mainloop()
    return result


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


def emit_permission_result(result: dict) -> None:
    action = result.get("action")
    if action == "allow":
        decision = {"behavior": "allow"}
    elif action == "allow_remember":
        decision = {"behavior": "allow"}
        suggestion = result.get("suggestion")
        if suggestion:
            decision["updatedPermissions"] = [suggestion]
    elif action == "deny":
        decision = {
            "behavior": "deny",
            "message": "Denied from Claude Code popup hook.",
            "interrupt": True,
        }
    else:
        # No decision: let Claude Code show its normal terminal permission prompt.
        emit_json({"suppressOutput": True})
        return

    emit_json(
        {
            "hookSpecificOutput": {
                "hookEventName": "PermissionRequest",
                "decision": decision,
            },
            "suppressOutput": True,
        }
    )


def main(argv: list[str]) -> int:
    mode = argv[1] if len(argv) > 1 else "notification"

    try:
        if mode == "permission":
            result = permission_dialog(read_payload())
            emit_permission_result(result)
        elif mode == "notification":
            notification_popup(read_payload())
            emit_json({"suppressOutput": True})
        elif mode == "test":
            write_stdout_text("popup_hook.py ok")
        else:
            emit_json({"suppressOutput": True})
    except Exception as exc:
        # Hooks should not break Claude Code. Surface the issue as context if needed.
        emit_json(
            {
                "systemMessage": "Claude Code popup hook failed: " + str(exc),
                "suppressOutput": False,
            }
        )
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))

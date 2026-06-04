# claude-popup-hooks

个人 Claude Code 桌面弹窗 hooks 仓库。

当前包含一个 Windows 桌面弹窗 hook：把 Claude Code 的权限申请和空闲通知转成可交互的系统弹窗，方便在离开终端或多窗口工作时及时处理。

## Hooks

### `popup_hook.py`

功能：

- `PermissionRequest`：在 Claude Code 请求工具权限时弹出窗口。
  - **Yes**：本次工具调用直接通过。
  - **Yes, don't ask again**：本次通过，并尽量应用 Claude Code 提供的 `permission_suggestions`，减少后续重复确认。
  - **No**：本次工具调用被拒绝。
  - **Terminal**：不在弹窗中决策，回退到 Claude Code 原始终端权限确认。
- `Notification` / `idle_prompt`：Claude Code 任务结束进入空闲等待时弹出通知。

特点：

- 面向 Windows 使用体验优化，提供更接近桌面应用的卡片式弹窗界面。
- 使用 Python 标准库 `tkinter`，不需要安装第三方依赖。
- hook 出错时不会中断 Claude Code 主流程。

## 环境要求

- Windows
- Python 3.8+（建议 3.10+）
- Python 自带 `tkinter`
- Claude Code 支持 hooks 的版本

检查 Python 和 `tkinter`：

```bash
python --version
python - <<'PY'
import tkinter
print('tkinter ok')
PY
```

## 安装

可以把本仓库 clone 到任意本地目录，例如：

```bash
git clone https://github.com/<your-github-username>/claude-popup-hooks.git <your-local-hooks-dir>
```

也可以直接下载 `popup_hook.py` 到任意本地目录。

## Claude Code 全局配置示例

编辑全局配置文件：

```text
C:\Users\<你的用户名>\.claude\settings.json
```

加入或合并以下配置。注意把路径改成你的实际路径：

```json
{
  "hooks": {
    "PermissionRequest": [
      {
        "matcher": ".*",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": [
              "<your-local-hooks-dir>\\popup_hook.py",
              "permission"
            ],
            "timeout": 600,
            "statusMessage": "等待弹窗权限确认..."
          }
        ]
      }
    ],
    "Notification": [
      {
        "matcher": "idle_prompt",
        "hooks": [
          {
            "type": "command",
            "command": "python",
            "args": [
              "<your-local-hooks-dir>\\popup_hook.py",
              "notification"
            ],
            "timeout": 300,
            "statusMessage": "显示空闲通知弹窗..."
          }
        ]
      }
    ]
  }
}
```

如果你的 `settings.json` 已经有其它配置，不要整体替换，手动把 `hooks` 部分合并进去。

## 路径填写说明

请把配置示例中的 `<your-local-hooks-dir>` 替换为你实际保存本仓库的本地目录。例如 Windows 路径需要在 JSON 字符串中使用双反斜杠转义。

## 验证

验证脚本可运行：

```bash
python <your-local-hooks-dir>/popup_hook.py test
```

预期输出：

```text
popup_hook.py ok
```

验证 `settings.json` 被 Claude Code 重新加载后，可以通过触发一次需要权限的工具调用观察弹窗。若当前会话未生效，可打开 Claude Code 的 `/hooks` 菜单或重启 Claude Code。

## 设计说明

`PermissionRequest` hook 会从标准输入读取 Claude Code 传入的 JSON，其中通常包含：

- `hook_event_name`
- `tool_name`
- `tool_input`
- `permission_suggestions`

当用户在弹窗中选择：

- `Yes`：输出 `PermissionRequest` 的 `allow` 决策。
- `Yes, don't ask again`：输出 `allow` 决策，并在收到 Claude Code `permission_suggestions` 时把第一条建议写入 `updatedPermissions`，相当于接受 Claude Code 给出的“以后不再询问”权限更新。
- `No`：输出 `PermissionRequest` 的 `deny` 决策。
- `Terminal`：不输出权限决策，让 Claude Code 使用原始权限提示继续处理。

> 注意：`Yes, don't ask again` 依赖 Claude Code 在 `PermissionRequest` 输入中提供 `permission_suggestions`。如果当前请求没有建议规则，该按钮会退化为仅允许本次。

`Notification` hook 用于处理 `idle_prompt`，只负责弹窗提醒，不阻塞或修改 Claude Code 的后续行为。

## License

MIT

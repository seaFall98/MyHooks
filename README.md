# MyHooks

个人 Claude Code hooks 集中管理仓库。

当前包含一个 Windows 桌面弹窗 hook：把 Claude Code 的权限申请和空闲通知转成可交互的系统弹窗，方便在离开终端或多窗口工作时及时处理。

## Hooks

### `popup_hook.py`

功能：

- `PermissionRequest`：在 Claude Code 请求工具权限时弹出窗口。
  - **允许本次**：本次工具调用直接通过。
  - **拒绝**：本次工具调用被拒绝。
  - **回到终端选择**：不在弹窗中决策，回退到 Claude Code 原始终端权限确认。
- `Notification` / `idle_prompt`：Claude Code 任务结束进入空闲等待时弹出通知。

特点：

- 面向 Windows 使用体验优化。
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
git clone https://github.com/<your-github-username>/MyHooks.git D:/MyCode/MyHooks
```

也可以直接下载 `popup_hook.py` 到本地目录。

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
              "D:\\MyCode\\MyHooks\\popup_hook.py",
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
              "D:\\MyCode\\MyHooks\\popup_hook.py",
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

## 当前用户配置示例

如果仓库位于：

```text
D:\MyCode\MyHooks
```

则脚本路径为：

```text
D:\MyCode\MyHooks\popup_hook.py
```

## 验证

验证脚本可运行：

```bash
python D:/MyCode/MyHooks/popup_hook.py test
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

- 允许：输出 `PermissionRequest` 的 `allow` 决策。
- 拒绝：输出 `PermissionRequest` 的 `deny` 决策。
- 回到终端选择：不输出权限决策，让 Claude Code 使用原始权限提示继续处理。

`Notification` hook 用于处理 `idle_prompt`，只负责弹窗提醒，不阻塞或修改 Claude Code 的后续行为。

## License

MIT

---
name: statusline-setup
description: >
  Use this agent to configure the user's Claude Code status line setting.
  Triggers on: "setup status line", "configure status bar", "install statusline"
version: 1.0.0
---

# Status Line Setup

Configure the Claude Code status line to use the win11-statusline plugin.

## Steps

1. **Find the plugin script path** — Locate `context-bar.py` relative to the user's plugin install:

   ```
   ~/.claude/plugins/local/win11-statusline/scripts/context-bar.py
   ```

2. **Read the user's `~/.claude/settings.json`** using the Read tool.

3. **Add or update the `statusLine` key** in settings.json:

   ```json
   "statusLine": {
     "type": "command",
     "command": "python <RESOLVED_ABSOLUTE_PATH>/scripts/context-bar.py"
   }
   ```

   - Resolve the absolute path dynamically (e.g., `C:/Users/<username>/.claude/plugins/local/win11-statusline/scripts/context-bar.py`)
   - Use forward slashes in the path

4. **Write the updated settings.json** using the Edit tool (preserve all existing keys).

5. **Verify** by reading back settings.json and confirming the `statusLine` key is present.

6. **Inform the user** to restart Claude Code for the status line to take effect.

## Optional: Theme Configuration

If the user wants a different color theme, edit the `COLOR = "orange"` line at the top of `context-bar.py`. Available themes:

- orange (default), blue, teal, green, lavender, rose, gold, slate, cyan, gray

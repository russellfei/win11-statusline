# win11-statusline

Windows-native status line plugin for Claude Code. Shows model, git status, context usage, and last message — no `jq` required.

Inspired by [ykdojo/claude-code-tips](https://github.com/ykdojo/claude-code-tips).

## Preview

```
Opus 4.6 | 📁project-dir | 🔀main (2 files uncommitted, synced 5m ago) | ██▄░░░░░░░ 25% of 200k tokens
💬 last user message here...
```

## Requirements

- Python 3.x (included with most Windows installs)
- Git (for branch/status info)
- Claude Code 2.0.65+

## Install

1. **Copy the plugin folder** to your Claude Code plugins directory:

   ```
   ~/.claude/plugins/local/win11-statusline/
   ```

2. **Add to marketplace.json** (`~/.claude/plugins/local/.claude-plugin/marketplace.json`):

   ```json
   {
     "name": "win11-statusline",
     "description": "Windows-native status line for Claude Code - shows model, git status, context usage, and last message. No jq required.",
     "version": "1.0.0",
     "author": { "name": "yangw" },
     "source": "./win11-statusline",
     "category": "development"
   }
   ```

3. **Enable the plugin** in `~/.claude/settings.json`:

   ```json
   "enabledPlugins": {
     "win11-statusline@local-plugins": true
   }
   ```

4. **Add the status line command** to `~/.claude/settings.json`:

   ```json
   "statusLine": {
     "type": "command",
     "command": "python C:/Users/YOUR_USERNAME/.claude/plugins/local/win11-statusline/scripts/context-bar.py"
   }
   ```

   Or run the setup skill: type `statusline-setup` in Claude Code.

5. **Restart Claude Code**.

## Color Themes

Edit the `COLOR` variable at the top of `scripts/context-bar.py`:

| Theme    | ANSI 256 Code | Description       |
|----------|---------------|-------------------|
| orange   | 173           | Warm amber (default) |
| blue     | 74            | Soft blue         |
| teal     | 66            | Muted teal        |
| green    | 71            | Forest green      |
| lavender | 139           | Light purple      |
| rose     | 132           | Dusty pink        |
| gold     | 136           | Dark gold         |
| slate    | 60            | Blue-gray         |
| cyan     | 37            | Bright cyan       |
| gray     | 245           | Neutral gray      |

## What It Shows

**Line 1:**
- Model name (e.g., `Opus 4.6`)
- Current directory name
- Git branch + uncommitted file count + sync status
- Context usage bar (10-cell, 3-level: █ full, ▄ half, ░ empty)

**Line 2:**
- Last user message from the conversation transcript

## How It Works

Claude Code pipes a JSON object to stdin containing model info, cwd, context window size, and transcript path. The script parses this with Python's `json` module (no `jq` needed), runs `git` commands for repo status, and reads the JSONL transcript for token usage and last message.

## License

MIT

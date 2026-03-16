#!/usr/bin/env python3
"""Claude Code status line - Windows 11 native, zero external deps.

Reads JSON from stdin (provided by Claude Code), outputs a 2-line status bar:
  Line 1: Model | Dir | Git branch (uncommitted, sync) | Context bar
  Line 2: Last user message from transcript

Inspired by ykdojo/claude-code-tips context-bar.sh.
Requires: Python 3.x, Git (for git info).
"""

import json
import os
import subprocess
import sys
import time

# ── Configuration ────────────────────────────────────────────────────────────
# Color theme: orange, blue, teal, green, lavender, rose, gold, slate, cyan, gray
COLOR = "orange"

# ── ANSI 256 color codes ────────────────────────────────────────────────────
C_RESET = "\033[0m"
C_GRAY = "\033[38;5;245m"
C_BAR_EMPTY = "\033[38;5;238m"

THEMES = {
    "orange":   "\033[38;5;173m",
    "blue":     "\033[38;5;74m",
    "teal":     "\033[38;5;66m",
    "green":    "\033[38;5;71m",
    "lavender": "\033[38;5;139m",
    "rose":     "\033[38;5;132m",
    "gold":     "\033[38;5;136m",
    "slate":    "\033[38;5;60m",
    "cyan":     "\033[38;5;37m",
    "gray":     "\033[38;5;245m",
}

C_ACCENT = THEMES.get(COLOR, C_GRAY)


def run_git(cwd, *args, timeout=5):
    """Run a git command, return stdout or empty string on failure."""
    try:
        r = subprocess.run(
            ["git", "-C", cwd] + list(args),
            capture_output=True, text=True, timeout=timeout,
        )
        return r.stdout.strip() if r.returncode == 0 else ""
    except Exception:
        return ""


def get_git_info(cwd):
    """Return (branch, status_string) or ("", "") if not a git repo."""
    if not cwd or not os.path.isdir(cwd):
        return "", ""

    branch = run_git(cwd, "branch", "--show-current")
    if not branch:
        return "", ""

    # Count uncommitted files
    porcelain = run_git(cwd, "--no-optional-locks", "status", "--porcelain", "-uall")
    lines = [l for l in porcelain.splitlines() if l.strip()] if porcelain else []
    file_count = len(lines)

    # Sync status with upstream
    upstream = run_git(cwd, "rev-parse", "--abbrev-ref", "@{upstream}")
    if upstream:
        fetch_ago = format_fetch_age(cwd)
        counts = run_git(cwd, "rev-list", "--left-right", "--count", "HEAD...@{upstream}")
        if counts:
            parts = counts.split()
            ahead, behind = int(parts[0]), int(parts[1])
        else:
            ahead, behind = 0, 0

        if ahead == 0 and behind == 0:
            sync = f"synced {fetch_ago}" if fetch_ago else "synced"
        elif ahead > 0 and behind == 0:
            sync = f"{ahead} ahead"
        elif ahead == 0 and behind > 0:
            sync = f"{behind} behind"
        else:
            sync = f"{ahead} ahead, {behind} behind"
    else:
        sync = "no upstream"

    # Build git status string
    if file_count == 0:
        git_status = f"(0 files uncommitted, {sync})"
    elif file_count == 1:
        single_file = lines[0][3:]  # strip status prefix (e.g. " M ")
        git_status = f"({single_file} uncommitted, {sync})"
    else:
        git_status = f"({file_count} files uncommitted, {sync})"

    return branch, git_status


def format_fetch_age(cwd):
    """Return human-readable time since last git fetch, or empty string."""
    fetch_head = os.path.join(cwd, ".git", "FETCH_HEAD")
    if not os.path.isfile(fetch_head):
        return ""
    try:
        mtime = os.path.getmtime(fetch_head)
        diff = int(time.time() - mtime)
        if diff < 60:
            return "<1m ago"
        elif diff < 3600:
            return f"{diff // 60}m ago"
        elif diff < 86400:
            return f"{diff // 3600}h ago"
        else:
            return f"{diff // 86400}d ago"
    except OSError:
        return ""


def build_progress_bar(pct, bar_width=10):
    """Build a 3-level progress bar: full █, half ▄, empty ░."""
    pct = max(0, min(100, pct))
    bar = ""
    for i in range(bar_width):
        bar_start = i * 10
        progress = pct - bar_start
        if progress >= 8:
            bar += f"{C_ACCENT}\u2588{C_RESET}"   # █ full
        elif progress >= 3:
            bar += f"{C_ACCENT}\u2584{C_RESET}"   # ▄ half
        else:
            bar += f"{C_BAR_EMPTY}\u2591{C_RESET}" # ░ empty
    return bar


def get_context_info(data, transcript_path):
    """Calculate context percentage and build the bar string."""
    max_context = 200000
    try:
        cw = data.get("context_window", {})
        max_context = int(cw.get("context_window_size", 200000))
    except (TypeError, ValueError):
        pass
    max_k = max_context // 1000

    context_length = 0
    pct_prefix = "~"
    baseline = 20000

    if transcript_path and os.path.isfile(transcript_path):
        context_length = calc_tokens_from_transcript(transcript_path)

    if context_length > 0:
        pct = context_length * 100 // max_context
        pct_prefix = ""
    else:
        pct = baseline * 100 // max_context

    pct = max(0, min(100, pct))
    bar = build_progress_bar(pct)
    return f"{bar} {C_GRAY}{pct_prefix}{pct}% of {max_k}k tokens"


def calc_tokens_from_transcript(transcript_path):
    """Parse JSONL transcript line-by-line, return token count from last usage entry."""
    last_usage = None
    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                # Skip sidechains and API error messages
                if entry.get("isSidechain") or entry.get("isApiErrorMessage"):
                    continue
                msg = entry.get("message", {})
                usage = msg.get("usage") if isinstance(msg, dict) else None
                if usage:
                    last_usage = usage
    except OSError:
        return 0

    if not last_usage:
        return 0

    return (
        last_usage.get("input_tokens", 0)
        + last_usage.get("cache_read_input_tokens", 0)
        + last_usage.get("cache_creation_input_tokens", 0)
    )


def get_last_user_message(transcript_path, max_len):
    """Return the last meaningful user message text from the JSONL transcript."""
    if not transcript_path or not os.path.isfile(transcript_path):
        return ""

    skip_prefixes = ("[Request interrupted", "[Request cancelled")
    last_msg = ""

    try:
        with open(transcript_path, "r", encoding="utf-8", errors="replace") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if entry.get("type") != "user":
                    continue
                msg = entry.get("message", {})
                content = msg.get("content", "") if isinstance(msg, dict) else ""

                # Content can be string or array of content blocks
                if isinstance(content, list):
                    texts = [b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"]
                    text = " ".join(texts)
                elif isinstance(content, str):
                    text = content
                else:
                    continue

                # Normalize whitespace
                text = " ".join(text.split())
                if not text or any(text.startswith(p) for p in skip_prefixes):
                    continue
                last_msg = text
    except OSError:
        return ""

    if not last_msg:
        return ""

    if len(last_msg) > max_len:
        return last_msg[: max_len - 3] + "..."
    return last_msg


def main():
    try:
        data = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        data = {}

    model = "?"
    m = data.get("model", {})
    if isinstance(m, dict):
        model = m.get("display_name") or m.get("id") or "?"

    cwd = data.get("cwd", "")
    dirname = os.path.basename(cwd) if cwd else "?"

    branch, git_status = get_git_info(cwd)
    transcript_path = data.get("transcript_path", "")
    ctx = get_context_info(data, transcript_path)

    # Line 1: Model | Dir | Git | Context
    parts = [f"{C_ACCENT}{model}{C_GRAY}", f"\U0001f4c1{dirname}"]
    if branch:
        parts.append(f"\U0001f500{branch} {git_status}")
    parts.append(ctx + C_RESET)
    line1 = " | ".join(parts)
    print(line1, flush=True)

    # Line 2: Last user message (calculate max_len from plain text width)
    plain = f"{model} | \U0001f4c1{dirname}"
    if branch:
        plain += f" | \U0001f500{branch} {git_status}"
    plain += f" | xxxxxxxxxx ?% of ???k tokens"
    max_len = len(plain)
    last_msg = get_last_user_message(transcript_path, max_len)
    if last_msg:
        print(f"\U0001f4ac {last_msg}", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Status line must never crash Claude Code
        pass

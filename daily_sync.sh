#!/bin/zsh
# daily_sync.sh: every morning, make the student pages match Bianca's Google Calendar (next class + booked classes),
# then publish if anything changed. Started by launchd (~/Library/LaunchAgents/com.realenglisherrors.dailysync.plist).
# Log: private/daily_sync.log. Payments are not touched here (they come from the board / Bianca).
cd "$(dirname "$0")" || exit 1
mkdir -p private
CLAUDE=$(ls -d "$HOME"/.vscode/extensions/anthropic.claude-code-*/resources/native-binary/claude 2>/dev/null | sort -V | tail -1)
[ -x "$CLAUDE" ] || { echo "$(date) claude program not found" >> private/daily_sync.log; exit 1; }
START=$(date +%Y-%m-%dT00:00:00); END=$(date -v+28d +%Y-%m-%dT00:00:00)
PROMPT="Daily sync of the Real English Errors student pages (this folder is the repo). Do exactly these steps and nothing else.
1) Call the Google Calendar list_events tool with startTime $START, endTime $END, orderBy startTime, pageSize 250 (no timeZone). The result is large and gets saved to a file: note that file's path.
2) Run: python3 sync_calendar.py <that file path> --apply
3) Run: git status --porcelain s index.html . If there are changes: git add s index.html, then git commit -m 'Daily calendar sync', then git push. If there are none, do not commit.
4) Reply with one line: what changed, or 'no changes'.
Never edit other files. Never add prices or amounts anywhere."
echo "=== $(date) ===" >> private/daily_sync.log
"$CLAUDE" -p "$PROMPT" --max-turns 15 \
  --allowedTools "mcp__claude_ai_Google_Calendar__list_events" "Bash(python3 sync_calendar.py:*)" "Bash(git status --porcelain s index.html .)" "Bash(git add s index.html)" "Bash(git commit -m:*)" "Bash(git push)" "Read" < /dev/null >> private/daily_sync.log 2>&1
echo "exit $?" >> private/daily_sync.log

#!/usr/bin/env bash
set -euo pipefail

task_file="${1:?usage: ./run.sh <task-file>}"
cd -- "$(dirname -- "$0")"

if [[ -z ${CS146S_GATEWAY_URL:-} ||
      ${ANTHROPIC_BASE_URL:-} != "${CS146S_GATEWAY_URL:-}/anthropic" ]]; then
  printf '%s\n' 'Start this entry point through the course practice runner or grader.' >&2
  exit 1
fi

ticket=$(cat -- "$task_file")

run_report() {
  CLAUDE_CODE_SAFE_MODE=1 CLAUDE_CODE_PROMPT_CACHE_TTL=5m \
    claude -p $'Complete only the impact report for this ticket.\n\n'"$ticket" \
      --model claude-haiku-5-5 \
      --effort medium \
      --system-prompt "$(cat prompts/impact.md)" \
      --tools 'Bash,Edit,Glob,Grep,Read,Write' \
      --strict-mcp-config \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --output-format stream-json --verbose
}

run_repair() {
  CLAUDE_CODE_SAFE_MODE=1 CLAUDE_CODE_PROMPT_CACHE_TTL=5m \
    claude -p $'Complete only the service repair for this ticket.\n\n'"$ticket" \
      --model claude-sonnet-5-5 \
      --effort high \
      --system-prompt "$(cat prompts/repair.md)" \
      --tools 'Bash,Edit,Glob,Grep,Read,Write' \
      --strict-mcp-config \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --output-format stream-json --verbose
}

run_report &
report_pid=$!
run_repair &
repair_pid=$!

report_status=0
wait "$report_pid" || report_status=$?
if (( report_status == 0 )) && ! python3 -m json.tool out/impact.json >/dev/null; then
  report_status=1
fi

wait "$repair_pid"
exit "$report_status"

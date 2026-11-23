#!/usr/bin/env bash
set -euo pipefail

task_file="${1:?usage: ./run.sh <task-file>}"
cd -- "$(dirname -- "$0")"

if [[ -z ${CS146S_GATEWAY_URL:-} || ${ANTHROPIC_BASE_URL:-} != "${CS146S_GATEWAY_URL:-}/anthropic" ]]; then
  printf '%s\n' 'Start this entry point through the course practice runner or grader.' >&2
  exit 1
fi

# Practice can use a subscription login. Safe mode keeps authentication and
# skips personal instructions, hooks, plugins, and memory.
export CLAUDE_CODE_SAFE_MODE=1
export CLAUDE_CODE_PROMPT_CACHE_TTL=5m

ticket=$(cat -- "$task_file")

run_stage() {
  local model=$1
  local prompt_file=$2
  local instruction=$3
  claude -p "$instruction"$'\n\n'"$ticket" \
    --model "$model" \
    --effort high \
    --system-prompt "$(cat -- "$prompt_file")" \
    --tools 'Bash,Edit,Glob,Grep,Read,Write' \
    --strict-mcp-config \
    --no-session-persistence \
    --permission-mode bypassPermissions \
    --output-format stream-json --verbose
}

run_stage claude-haiku-5-5 prompts/impact.md 'Complete only the impact report for this ticket.' &
report_pid=$!
run_stage claude-sonnet-5-5 prompts/repair.md 'Complete only the service repair for this ticket.' &
repair_pid=$!

report_status=0
wait "$report_pid" || report_status=$?
if (( report_status == 0 )) && ! python3 -m json.tool out/impact.json >/dev/null; then
  report_status=1
fi

wait "$repair_pid"
exit "$report_status"

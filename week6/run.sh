#!/usr/bin/env bash
set -euo pipefail

task_file="${1:?usage: ./run.sh <task-file>}"
cd -- "$(dirname -- "$0")"

if [[ -z ${CS146S_GATEWAY_URL:-} ||
      ${ANTHROPIC_BASE_URL:-} != "${CS146S_GATEWAY_URL:-}/anthropic" ||
      ${OPENAI_BASE_URL:-} != "${CS146S_GATEWAY_URL:-}/openai/v1" ]]; then
  printf '%s\n' 'Start this entry point through the course practice runner or grader.' >&2
  exit 1
fi

: "${CODEX_HOME:?the course runner must configure Codex}"
ticket=$(cat -- "$task_file")

run_report() {
  CLAUDE_CODE_SAFE_MODE=1 CLAUDE_CODE_PROMPT_CACHE_TTL=5m \
    claude -p $'Complete only the impact report for this ticket.\n\n'"$ticket" \
      --model claude-haiku-5-5 \
      --effort high \
      --system-prompt "$(cat prompts/impact.md)" \
      --tools 'Bash,Edit,Glob,Grep,Read,Write' \
      --strict-mcp-config \
      --no-session-persistence \
      --permission-mode bypassPermissions \
      --output-format stream-json --verbose
}

run_repair() {
  local repair_prompt
  repair_prompt=$(cat prompts/repair.md)
  codex exec -m gpt-6.1-terra \
    -c 'model_provider="cs146s"' \
    -c 'model_reasoning_effort="high"' \
    -c 'web_search="disabled"' \
    --disable apps --disable plugins --disable remote_plugin \
    --dangerously-bypass-approvals-and-sandbox \
    --skip-git-repo-check --ephemeral --json \
    $'Complete only the service repair for this ticket.\n\n'"$repair_prompt"$'\n\n'"$ticket"
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

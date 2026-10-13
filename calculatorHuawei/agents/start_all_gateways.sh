#!/bin/bash
# start_all_gateways.sh
# 一次性启动 5 个 agent 的 gateway。
# 用法: bash D:/huawei/Demo/calculatorHuawei/agents/start_all_gateways.sh

set -e

HERMES="/c/Users/26909/AppData/Local/hermes/hermes-agent/venv/Scripts/hermes"
PROFILES=(
  "dev-01:8100"
  "rev-01:8101"
  "analysis:8103"
  "skillopt-01:8104"
  "dev-02:8105"
)
WORK_DIR="D:/huawei/Demo/calculatorHuawei"

echo "=========================================="
echo "  启动 5 个 agent gateway"
echo "  Work dir: $WORK_DIR"
echo "=========================================="
echo ""

cd "$WORK_DIR" || exit 1

for entry in "${PROFILES[@]}"; do
  PROFILE="${entry%%:*}"
  PORT="${entry##*:}"
  echo "────────────────────────────────────────"
  echo "[→] $PROFILE  (port $PORT)"

  # 1. 检查 profile dir
  PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE"
  if [ ! -d "$PROFILE_DIR" ]; then
    echo "[ERROR] $PROFILE_DIR 不存在, 跳过"
    continue
  fi

  # 2. 检查 .env + token 占位
  ENV_FILE="$PROFILE_DIR/.env"
  if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] $ENV_FILE 不存在, 跳过"
    continue
  fi
  if grep -qE "PENDING_FILL|PENDING_USER_TO_FILL" "$ENV_FILE"; then
    echo "[WARN] $PROFILE/.env 有未填占位符:"
    grep -nE "PENDING_FILL|PENDING_USER_TO_FILL" "$ENV_FILE" | head -3
    echo "       请先填入再启动"
    continue
  fi

  # 3. 切换 profile + 启动 gateway（后台）
  "$HERMES" profile use "$PROFILE" >/dev/null 2>&1
  if "$HERMES" gateway start --port "$PORT" >/dev/null 2>&1; then
    echo "[OK] Gateway 启动: http://localhost:$PORT"
  else
    echo "[WARN] Gateway 启动失败（可能已在跑）"
  fi
  echo ""
done

echo "=========================================="
echo "  所有 gateway 已就绪"
echo ""
echo "  健康检查:"
for entry in "${PROFILES[@]}"; do
  PROFILE="${entry%%:*}"
  PORT="${entry##*:}"
  HEALTH=$(curl -s "http://localhost:$PORT/health" 2>/dev/null || echo "down")
  echo "    $PROFILE (port $PORT): $HEALTH"
done
echo ""
echo "  详细日志: hermes gateway status --profile <name>"
echo "=========================================="

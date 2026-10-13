#!/bin/bash
# skillopt-01 - 启动数字员工
# 上岗时间: 2026-06-16
# 角色: skill-optimizer (自定义)

set -e

PROFILE_NAME="skillopt-01"
GATEWAY_PORT=8104
WORK_DIR="D:/huawei/Demo/calculatorHuawei"

echo "=========================================="
echo "  启动 skillopt-01 (skill-optimizer)"
echo "=========================================="

cd "$WORK_DIR" || exit 1

ENV_FILE="$HOME/.hermes/profiles/$PROFILE_NAME/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] $ENV_FILE 不存在"
    exit 1
fi
if grep -q "PENDING_USER_TO_FILL" "$ENV_FILE"; then
    echo "[ERROR] .env 中 Token 未填入"
    exit 1
fi
echo "[OK] .env 已配置"

hermes profile use "$PROFILE_NAME"
echo "[OK] 切换到 profile: $PROFILE_NAME"

echo "[→] 启动 Gateway (port $GATEWAY_PORT)..."
hermes gateway start --port "$GATEWAY_PORT" &
GATEWAY_PID=$!
echo "[OK] Gateway PID: $GATEWAY_PID"

echo "[→] 配置 CronJob（每 10 分钟轮询 Issues）..."
hermes cron create 30m poll_issues.py \
    --script "$HOME/.hermes/scripts/poll_issues.py" \
    --workdir "$WORK_DIR" \
    --profile "$PROFILE_NAME" 2>/dev/null || echo "[WARN] CronJob 已存在或创建失败"

echo ""
echo "=========================================="
echo "  skillopt-01 已启动"
echo "  Gateway: http://localhost:$GATEWAY_PORT"
echo "  Profile: $PROFILE_NAME"
echo "  角色: skill-optimizer (Skill 优化师)"
echo "  任务: 优化 skill 描述、流程、提示词"
echo "  协作: 与 analysis 互补（诊断 → 优化）"
echo "=========================================="

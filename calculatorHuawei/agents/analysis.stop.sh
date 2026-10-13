#!/bin/bash
# analysis - 停止数字员工

PROFILE_NAME="analysis"
GATEWAY_PORT=8103

echo "=========================================="
echo "  停止 analysis"
echo "=========================================="

# 1. 暂停 cron 任务
hermes cron pause --profile "$PROFILE_NAME" 2>/dev/null || echo "[INFO] 无活跃 cron 任务"

# 2. 停止 Gateway
hermes gateway stop --port "$GATEWAY_PORT" 2>/dev/null || echo "[INFO] Gateway 未在运行"

echo "[OK] analysis 已停止"

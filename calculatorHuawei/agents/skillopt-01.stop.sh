#!/bin/bash
# skillopt-01 - 停止数字员工

PROFILE_NAME="skillopt-01"
GATEWAY_PORT=8104

echo "=========================================="
echo "  停止 skillopt-01"
echo "=========================================="

hermes cron pause --profile "$PROFILE_NAME" 2>/dev/null || echo "[INFO] 无活跃 cron 任务"
hermes gateway stop --port "$GATEWAY_PORT" 2>/dev/null || echo "[INFO] Gateway 未在运行"

echo "[OK] skillopt-01 已停止"

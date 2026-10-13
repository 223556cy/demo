#!/bin/bash
# analysis - 启动数字员工 (首席诊断分析师 v3)
# 上岗时间: 2026-06-18
# 角色: research-analyst (法医诊断 + 技能优化接力)

set -e

PROFILE_NAME="analysis"
GATEWAY_PORT=8103
PROFILE_DIR="$HOME/.hermes/profiles/$PROFILE_NAME"
WORK_DIR="D:/huawei/Demo/calculatorHuawei"

echo "=========================================="
echo "  启动 analysis (首席诊断分析师 v3)"
echo "=========================================="

# 1. 切换到工作目录
cd "$WORK_DIR" || exit 1

# 2. 检查 profile dir + .env + 必填 token
if [ ! -d "$PROFILE_DIR" ]; then
    echo "[ERROR] $PROFILE_DIR 不存在, 请先 mkdir -p"
    exit 1
fi

ENV_FILE="$PROFILE_DIR/.env"
if [ ! -f "$ENV_FILE" ]; then
    echo "[ERROR] $ENV_FILE 不存在, 请从 dev-01/.env 复制并填入 littleleafAnalysis 的 GITHUB_TOKEN"
    exit 1
fi

# Token 占位符检查 (我们用 PENDING_FILL_* 标记)
if grep -qE "PENDING_FILL|PENDING_USER_TO_FILL" "$ENV_FILE"; then
    echo "[ERROR] .env 中有未填入的占位符 (PENDING_FILL_*):"
    grep -nE "PENDING_FILL|PENDING_USER_TO_FILL" "$ENV_FILE" | head -5
    echo ""
    echo "请编辑 $ENV_FILE 填入:"
    echo "  GITHUB_TOKEN=littleleafAnalysis 的 GitHub PAT"
    echo "  ANTHROPIC_API_KEY=跟 dev-01/.env 一样"
    echo "  KIMI_CN_API_KEY=跟 dev-01/.env 一样"
    exit 1
fi
echo "[OK] .env 已配置"

# 3. 检查 dispatch script
SCRIPT="$PROFILE_DIR/scripts/dispatch_analysis.py"
if [ ! -f "$SCRIPT" ]; then
    echo "[ERROR] $SCRIPT 不存在"
    exit 1
fi
echo "[OK] dispatch script 存在: $SCRIPT"

# 4. 切换到 analysis profile
hermes profile use "$PROFILE_NAME"
echo "[OK] 切换到 profile: $PROFILE_NAME"

# 5. 启动 Gateway (后台)
echo "[→] 启动 Gateway (port $GATEWAY_PORT)..."
hermes gateway start --port "$GATEWAY_PORT" &
GATEWAY_PID=$!
echo "[OK] Gateway PID: $GATEWAY_PID"

# 6. 注册 cron (每 10 分钟, no_agent 模式)
#    直接用 jobs.json (避免 hermes cron create 的 CLI 差异)
echo "[→] 注册 CronJob (每 10 分钟, no_agent, 跑 dispatch_analysis.py)..."
CRON_FILE="$PROFILE_DIR/cron/jobs.json"
if [ ! -f "$CRON_FILE" ]; then
    echo "[ERROR] $CRON_FILE 不存在"
    exit 1
fi
# 检查 jobs.json 里有没有 analysis 的 job
if grep -q "analysis Issue Forensic Worker" "$CRON_FILE"; then
    echo "[OK] jobs.json 已包含 analysis cron job"
else
    echo "[WARN] jobs.json 没有 analysis job, 请检查"
fi

# 尝试通过 hermes cron 重新加载 (如果 hermes 支持)
hermes cron load --profile "$PROFILE_NAME" 2>/dev/null || \
hermes cron reload 2>/dev/null || \
echo "[INFO] 未找到 hermes cron load/reload 命令, jobs.json 已就位, 启动后会由 hermes gateway 自动发现"

echo ""
echo "=========================================="
echo "  analysis 已启动"
echo "  Gateway: http://localhost:$GATEWAY_PORT"
echo "  Profile: $PROFILE_NAME"
echo "  角色: research-analyst (首席诊断分析师 v3)"
echo "  任务: 法医诊断 rev-01 close/reject 的 issue + session 对话分析"
echo "  触发: rev-01 finalize_review 后加 analysis:pending 标签"
echo "  Polling: 每 10 分钟"
echo "=========================================="

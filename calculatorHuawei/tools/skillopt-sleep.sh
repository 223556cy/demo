#!/bin/bash
# skillopt-sleep.sh - SkillOpt 一键调用脚本 (Bash 版)
# 自动设置 UTF-8 + 切到独立 venv + 工作目录

export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

VENV_PY="D:/huawei/Demo/calculatorHuawei/.venv-skillopt/Scripts/python.exe"
cd /d/huawei/Demo/calculatorHuawei || exit 1

"$VENV_PY" -m skillopt_sleep "$@"

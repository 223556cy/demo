@echo off
REM skillopt-sleep.cmd - SkillOpt 一键调用脚本
REM 自动设置 UTF-8 + 切到独立 venv + 工作目录

setlocal

REM 1. UTF-8 编码 (修复 Windows GBK bug)
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1

REM 2. venv 路径
set VENV_PY=D:\huawei\Demo\calculatorHuawei\.venv-skillopt\Scripts\python.exe

REM 3. 工作目录
cd /d D:\huawei\Demo\calculatorHuawei

REM 4. 调用
%VENV_PY% -m skillopt_sleep %*

endlocal

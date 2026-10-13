#!/usr/bin/env python3
"""
单个数字员工的定时任务配置脚本

用法：
    # 为指定 Profile 配置默认定时任务
    python3 setup_cron.py --profile dev-01

    # 自定义配置
    python3 setup_cron.py --profile dev-01 \\
        --poll "*/30 * * * *" \\
        --report "0 18 * * *" \\
        --evolve "0 2 * * *" \\
        --cleanup "0 20 * * *"

    # 通过 cron-config.yaml 配置
    python3 setup_cron.py --config cron-config.yaml

    # 列出当前任务
    python3 setup_cron.py --profile dev-01 --list

    # 移除所有任务
    python3 setup_cron.py --profile dev-01 --remove-all
"""

import argparse
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

import yaml


@dataclass
class CronJob:
    name: str
    schedule: str
    action: str
    params: Dict = field(default_factory=dict)
    description: str = ""


class CronManager:
    """管理单个 Agent 的定时任务。"""

    CRON_PATTERN = re.compile(
        r'^([0-9,*/-]+|\*|\*/[0-9]+)\s+'
        r'([0-9,*/-]+|\*|\*/[0-9]+)\s+'
        r'([0-9,*/-]+|\*|\*/[0-9]+)\s+'
        r'([0-9,*/-]+|\*|\*/[0-9]+)\s+'
        r'([0-9,*/-]+|\*|\*/[0-9]+)$'
    )

    NL_PATTERNS = {
        "每半小时": "*/30 * * * *",
        "每30分钟": "*/30 * * * *",
        "每小时": "0 * * * *",
        "每天": "0 0 * * *",
        "每天早上": "0 8 * * *",
        "每天中午": "0 12 * * *",
        "每天晚上": "0 18 * * *",
        "每天晚上8点": "0 20 * * *",
        "每天凌晨": "0 2 * * *",
    }

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run

    def log(self, message: str, level: str = "INFO"):
        prefix = {"INFO": "[ℹ]", "OK": "[✓]", "WARN": "[⚠]", "ERROR": "[✗]", "DRY": "[◌]"}
        print(f"{prefix.get(level, '[?]')} {message}")

    def nl_to_cron(self, natural: str) -> str:
        for pattern, cron in self.NL_PATTERNS.items():
            if pattern in natural:
                return cron
        return natural

    def run_hermes(self, profile: str, cmd: List[str]) -> Tuple[int, str, str]:
        """在指定 Profile 下运行 hermes 命令。"""
        if self.dry_run:
            self.log(f"[{profile}] 将执行: hermes {' '.join(cmd)}", "DRY")
            return 0, "", ""
        try:
            subprocess.run(["hermes", "profile", "use", profile], capture_output=True, timeout=10)
            result = subprocess.run(["hermes"] + cmd, capture_output=True, text=True, timeout=30)
            return result.returncode, result.stdout, result.stderr
        except Exception as e:
            return -1, "", str(e)

    def add_job(self, profile: str, job: CronJob) -> bool:
        if self.dry_run:
            self.log(f"[{profile}] 将添加: {job.name} ({job.schedule})", "DRY")
            return True

        rc, stdout, stderr = self.run_hermes(profile, [
            "cron", "add",
            "--name", job.name,
            "--schedule", job.schedule,
            "--command", job.action
        ])

        if rc == 0:
            self.log(f"[{profile}] {job.name} 已添加", "OK")
            return True
        else:
            self.log(f"[{profile}] {job.name} 添加失败: {stderr}", "ERROR")
            return False

    def list_jobs(self, profile: str) -> List[Dict]:
        rc, stdout, _ = self.run_hermes(profile, ["cron", "list"])
        if rc != 0:
            return []
        jobs = []
        for line in stdout.strip().splitlines():
            parts = line.split(None, 2)
            if len(parts) >= 3:
                jobs.append({"name": parts[0], "schedule": parts[1], "command": parts[2]})
        return jobs

    def remove_all(self, profile: str) -> bool:
        if self.dry_run:
            self.log(f"[{profile}] 将移除所有任务", "DRY")
            return True
        rc, _, _ = self.run_hermes(profile, ["cron", "remove", "--all"])
        return rc == 0

    def setup_defaults(self, profile: str, poll: str, report: str, evolve: str, cleanup: str):
        """配置默认定时任务。"""
        self.log(f"\n为 {profile} 配置定时任务")
        self.log(f"{'='*40}")

        jobs = [
            CronJob("task-polling", self.nl_to_cron(poll), "github issue scan --assignee self --auto-process", {}, "轮询 GitHub Issues"),
            CronJob("daily-report", self.nl_to_cron(report), "report daily-summary", {}, "每日工作摘要"),
            CronJob("self-evolution", self.nl_to_cron(evolve), "memory extract-skills --save", {}, "自我进化"),
            CronJob("memory-cleanup", self.nl_to_cron(cleanup), "memory archive --older-than 30d", {}, "记忆清理"),
        ]

        for job in jobs:
            self.add_job(profile, job)

        self.log(f"\n完成。当前任务:")
        for job in self.list_jobs(profile):
            self.log(f"  - {job['name']}: {job['schedule']}")


def main():
    parser = argparse.ArgumentParser(description="数字员工定时任务配置")
    parser.add_argument("--profile", "-p", help="Agent Profile 名称")
    parser.add_argument("--config", "-c", help="cron-config.yaml 路径")
    parser.add_argument("--poll", default="*/30 * * * *", help="Issue 轮询频率")
    parser.add_argument("--report", default="0 18 * * *", help="日报时间")
    parser.add_argument("--evolve", default="0 2 * * *", help="自我进化时间")
    parser.add_argument("--cleanup", default="0 20 * * *", help="记忆清理时间")
    parser.add_argument("--list", action="store_true", help="列出当前任务")
    parser.add_argument("--remove-all", action="store_true", help="移除所有任务")
    parser.add_argument("--dry-run", action="store_true", help="试运行")

    args = parser.parse_args()

    manager = CronManager(dry_run=args.dry_run)

    if args.list and args.profile:
        jobs = manager.list_jobs(args.profile)
        for job in jobs:
            print(f"  {job['name']}: {job['schedule']} -> {job['command']}")
        return

    if args.remove_all and args.profile:
        manager.remove_all(args.profile)
        return

    if args.profile:
        manager.setup_defaults(args.profile, args.poll, args.report, args.evolve, args.cleanup)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
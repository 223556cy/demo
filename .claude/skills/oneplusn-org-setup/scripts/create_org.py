#!/usr/bin/env python3
"""
开子公司辅助脚本 - 生成 handoff.yaml 交接文件

仅收集老板和组织信息，生成交接配置。不涉及任何数字员工。
支持 macOS（默认）和 Windows。

用法：
    # 检测依赖
    python3 create_org.py --check-deps

    # 交互式模式
    python3 create_org.py --interactive

    # 命令行参数
    python3 create_org.py \
        --boss-username oneplusn-boss \
        --boss-email oneplusn_boss@163.com \
        --org-name oneplusn-team \
        --repo-name agent_workflow

    # 指定平台
    python3 create_org.py --check-deps --platform windows
"""

import argparse
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

import yaml


# ============ 依赖检测 ============

DEPENDENCIES = {
    "required": [
        {"name": "hermes", "cmd": "hermes", "arg": "--version",
         "desc": "1+N 数字员工框架（必须）",
         "macos": "brew tap NousResearch/hermes && brew install hermes-agent",
         "windows": "参考 https://github.com/NousResearch/hermes-agent 官方文档"},
        {"name": "python3", "cmd": "python3", "arg": "--version",
         "desc": "Python 3.10+",
         "macos": "brew install python@3.11",
         "windows": "winget install Python.Python.3.11 或官网下载"},
        {"name": "git", "cmd": "git", "arg": "--version",
         "desc": "版本控制工具",
         "macos": "brew install git",
         "windows": "winget install Git.Git"},
    ],
    "python_libs": [
        {"name": "PyYAML", "import": "yaml",
         "desc": "YAML 配置文件解析（必须）",
         "install": "pip3 install pyyaml"},
    ],
    "recommended": [
        {"name": "gh", "cmd": "gh", "arg": "--version",
         "desc": "GitHub 命令行工具（推荐）",
         "macos": "brew install gh",
         "windows": "winget install GitHub.cli"},
    ]
}


def check_tool(name: str, cmd: str, arg: str) -> tuple:
    """检测单个工具是否安装。返回 (是否安装, 版本信息)"""
    tool_path = shutil.which(cmd)
    if not tool_path:
        return False, "未找到"
    try:
        result = subprocess.run([cmd, arg], capture_output=True, text=True, timeout=10)
        version = result.stdout.strip() or result.stderr.strip()
        # 取第一行
        version = version.splitlines()[0] if version else "未知版本"
        return True, version
    except Exception:
        return False, "检测失败"


def check_python_lib(name: str, import_name: str) -> tuple:
    """检测 Python 库是否安装。返回 (是否安装, 版本信息)"""
    try:
        result = subprocess.run(
            ["python3", "-c", f"import {import_name}; print({import_name}.__version__)"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            version = result.stdout.strip()
            return True, version
        return False, "未安装"
    except Exception:
        return False, "检测失败"


def check_dependencies(target_platform: str = "macos") -> dict:
    """检测所有依赖。返回检测结果字典。"""
    results = {"required": {}, "python_libs": {}, "recommended": {}, "all_ok": True, "platform": target_platform}

    print(f"\n检测平台: {target_platform.upper()}")
    print("=" * 50)

    for category in ["required", "recommended"]:
        print(f"\n【{'必须' if category == 'required' else '推荐'}安装】")
        for dep in DEPENDENCIES[category]:
            installed, version = check_tool(dep["name"], dep["cmd"], dep["arg"])
            results[category][dep["name"]] = {
                "installed": installed,
                "version": version,
                "install_cmd": dep.get(target_platform, dep.get("macos", "")),
                "desc": dep["desc"]
            }
            status = "✓ 已安装" if installed else "✗ 未安装"
            print(f"  {dep['name']:12s} {status:10s} {version}")
            if category == "required" and not installed:
                results["all_ok"] = False

    # Python 库检测
    print(f"\n【Python 库】")
    for dep in DEPENDENCIES.get("python_libs", []):
        installed, version = check_python_lib(dep["name"], dep["import"])
        results["python_libs"][dep["name"]] = {
            "installed": installed,
            "version": version,
            "install_cmd": dep.get("install", ""),
            "desc": dep["desc"]
        }
        status = "✓ 已安装" if installed else "✗ 未安装"
        print(f"  {dep['name']:12s} {status:10s} {version}")
        if not installed:
            results["all_ok"] = False

    return results


def print_install_guide(results: dict):
    """打印安装指引。"""
    platform_name = results["platform"]

    print(f"\n{'=' * 50}")
    print("安装指引")
    print(f"{'=' * 50}")

    # 先检查 Hermes
    hermes_info = results["required"].get("hermes", {})
    if not hermes_info.get("installed"):
        print("\n⚠️  Hermes 未安装！这是 1+N 数字员工框架的核心，必须先安装。")
        print(f"\n  {platform_name.upper()} 安装命令:")
        print(f"    {hermes_info.get('install_cmd', '')}")
        print("\n  安装完成后重新运行本脚本。")
        print("  官方文档: https://github.com/NousResearch/hermes-agent")
        return False

    # Python 库检测
    missing_libs = []
    for name, info in results.get("python_libs", {}).items():
        if not info["installed"]:
            missing_libs.append(info)

    if missing_libs:
        print(f"\n以下 Python 库未安装，必须安装后才能继续：\n")
        for info in missing_libs:
            print(f"  {info['desc']}")
            print(f"  安装: {info['install_cmd']}\n")

    # 其他未安装的依赖
    missing = []
    for category in ["required", "recommended"]:
        for name, info in results[category].items():
            if name == "hermes":
                continue
            if not info["installed"]:
                missing.append(info)

    if missing:
        print(f"\n以下工具未安装，建议安装后再继续：\n")
        for info in missing:
            print(f"  {info['desc']}")
            print(f"  安装: {info['install_cmd']}\n")

    if missing_libs:
        return False

    return True


# ============ 交互式引导 ============

def ask(question: str, default: str = "") -> str:
    """向用户提问并获取回答。"""
    try:
        if default:
            response = input(f"{question} [{default}]: ").strip()
            return response if response else default
        return input(f"{question}: ").strip()
    except EOFError:
        return default


def ask_bool(question: str) -> bool:
    """询问是/否问题。"""
    try:
        while True:
            response = input(f"{question} (y/n): ").strip().lower()
            if response in ("y", "yes", "是"):
                return True
            if response in ("n", "no", "否", ""):
                return False
            print("  请输入 y 或 n")
    except EOFError:
        return False


def interactive_mode(target_platform: str):
    """交互式引导模式。"""
    print("\n" + "=" * 50)
    print("开子公司 - 信息收集")
    print("=" * 50)
    print(f"\n平台: {target_platform.upper()}")
    print("本工具将收集老板和组织信息，生成交接文件 handoff.yaml。")
    print("每一步都会询问你是否已有对应资源，如有可直接复用。\n")

    # 第1步：邮箱
    print("-" * 50)
    print("第1步：老板邮箱")
    print("-" * 50)
    has_email = ask_bool("你有可用的邮箱吗？（推荐 163 邮箱）")
    if has_email:
        email = ask("请输入邮箱地址")
    else:
        print("\n[指引] 请注册 163 邮箱：")
        print("  1. 访问 https://mail.163.com/")
        print("  2. 点击\"注册新账号\" → \"注册字母邮箱\"")
        print("  3. 填写邮箱地址、设置密码、手机验证")
        print("  4. 完成注册后回到这里\n")
        email = ask("请输入注册好的邮箱地址")

    # 第2步：GitHub
    print("\n" + "-" * 50)
    print("第2步：老板 GitHub 账号")
    print("-" * 50)
    has_github = ask_bool("你有 GitHub 账号吗？")
    if has_github:
        username = ask("请输入 GitHub 用户名")
    else:
        print("\n[指引] 请创建 GitHub 账号：")
        print("  1. 访问 https://github.com/signup")
        print(f"  2. 使用邮箱 {email} 注册")
        print("  3. 设置用户名、密码，完成邮箱验证")
        print("  4. 完成注册后回到这里\n")
        username = ask("请输入注册好的 GitHub 用户名")

    # 第3步：Organization
    print("\n" + "-" * 50)
    print("第3步：GitHub Organization（子公司）")
    print("-" * 50)
    has_org = ask_bool("你有 GitHub Organization 吗？")
    if has_org:
        org_name = ask("请输入 Organization 名称")
    else:
        print("\n[指引] 请创建 Organization：")
        print(f"  1. 用 {username} 登录 GitHub")
        print("  2. 头像 → 你的组织 → 新建组织 → 创建免费组织")
        print("  3. 填写组织名称、联系邮箱")
        print("  4. 跳过成员邀请，完成创建")
        print("  5. 设置 → Member privileges → Base permissions: Read\n")
        org_name = ask("请输入创建好的 Organization 名称")

    # 第4步：仓库
    print("\n" + "-" * 50)
    print("第4步：团队仓库")
    print("-" * 50)
    has_repo = ask_bool("你的组织下已有协作仓库吗？")
    if has_repo:
        repo_name = ask("请输入仓库名称")
    else:
        print("\n[指引] 请创建仓库：")
        print(f"  1. 进入 https://github.com/{org_name}")
        print("  2. Repositories → New")
        print("  3. 名称：agent_workflow（可自定义）")
        print("  4. Private ✓、Initialize with README ✓\n")
        repo_name = ask("请输入创建好的仓库名称", "agent_workflow")

    # 第5步：Token（可选）
    print("\n" + "-" * 50)
    print("第5步：Personal Access Token（可选）")
    print("-" * 50)
    has_token = ask_bool("你已生成 GitHub Token 了吗？（可以后续再生成）")
    token = ""
    if has_token:
        token = ask("请输入 Token（ghp_...）")

    # 汇总
    print("\n" + "=" * 50)
    print("信息汇总")
    print("=" * 50)
    print(f"  邮箱：{email}")
    print(f"  GitHub：{username}")
    print(f"  Organization：{org_name}")
    print(f"  仓库：{repo_name}")
    print(f"  Token：{'已提供' if token else '未提供（后续可补）'}")

    if not ask_bool("\n确认信息无误，生成交接文件？"):
        print("已取消。")
        return

    output_path = ask("输出文件路径", "handoff.yaml")
    generate_handoff(email, username, org_name, repo_name, token, output_path)


# ============ 交接文件生成 ============

def generate_handoff(email: str, username: str, org_name: str, repo_name: str, token: str, output_path: str):
    """生成 handoff.yaml 交接文件。"""
    handoff = {
        "metadata": {
            "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "stage": "org-setup-complete",
            "next_stage": "agent-onboarding"
        },
        "organization": {
            "name": org_name,
            "url": f"https://github.com/{org_name}"
        },
        "repository": {
            "name": repo_name,
            "url": f"https://github.com/{org_name}/{repo_name}",
            "issues_url": f"https://github.com/{org_name}/{repo_name}/issues"
        },
        "boss": {
            "github_username": username,
            "email": email
        }
    }

    if token:
        handoff["boss"]["token"] = token

    with open(output_path, 'w') as f:
        yaml.dump(handoff, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n交接文件已生成: {output_path}")
    print(f"  组织: {org_name}")
    print(f"  仓库: {org_name}/{repo_name}")
    print(f"  老板: {username} ({email})")
    print(f"\n下一阶段'数字员工上岗'将使用此文件。")


def generate_sample():
    """生成示例配置。"""
    sample = {
        "organization": {
            "name": "yourname-team",
            "url": "https://github.com/yourname-team"
        },
        "repository": {
            "name": "agent_workflow",
            "url": "https://github.com/yourname-team/agent_workflow"
        },
        "boss": {
            "github_username": "yourname-boss",
            "email": "yourname_boss@163.com"
        }
    }

    print("# 示例 handoff.yaml 结构：\n")
    print(yaml.dump(sample, default_flow_style=False, allow_unicode=True, sort_keys=False))


def main():
    parser = argparse.ArgumentParser(
        description="开子公司辅助脚本 - 仅生成交接文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用方式:
  1. 检测依赖（推荐先执行）：
     %(prog)s --check-deps

  2. 交互式引导：
     %(prog)s --interactive

  3. 命令行参数：
     %(prog)s --boss-username yourname-boss \\
              --boss-email yourname_boss@163.com \\
              --org-name yourname-team

  4. 指定平台（默认 macOS）：
     %(prog)s --check-deps --platform windows
        """
    )

    parser.add_argument("--check-deps", action="store_true", help="检测依赖是否安装")
    parser.add_argument("--platform", choices=["macos", "windows"],
                        default="macos", help="目标平台（默认 macOS）")
    parser.add_argument("--interactive", "-i", action="store_true", help="交互式引导模式")
    parser.add_argument("--boss-username", help="老板 GitHub 用户名")
    parser.add_argument("--boss-email", help="老板邮箱")
    parser.add_argument("--boss-token", default="", help="老板 GitHub Token（可选）")
    parser.add_argument("--org-name", help="Organization 名称")
    parser.add_argument("--repo-name", default="agent_workflow", help="仓库名称")
    parser.add_argument("--output", "-o", default="handoff.yaml", help="输出文件路径")
    parser.add_argument("--sample", action="store_true", help="显示示例配置")

    args = parser.parse_args()

    # 检测依赖模式
    if args.check_deps:
        results = check_dependencies(args.platform)
        ok = print_install_guide(results)
        if not ok:
            sys.exit(1)
        if not results["all_ok"]:
            print("\n⚠️  部分依赖未安装，建议安装后再继续。")
            sys.exit(1)
        print("\n✓ 所有依赖已就绪，可以继续。")
        return

    if args.sample:
        generate_sample()
        return

    if args.interactive:
        interactive_mode(args.platform)
        return

    # 命令行参数模式
    if args.boss_username and args.boss_email and args.org_name:
        generate_handoff(
            email=args.boss_email,
            username=args.boss_username,
            org_name=args.org_name,
            repo_name=args.repo_name,
            token=args.boss_token,
            output_path=args.output
        )
    else:
        print("错误: 缺少必要参数。")
        print("使用 --check-deps 检测依赖，或 --interactive 交互式引导。")
        print("使用 --help 查看完整帮助。")
        sys.exit(1)


if __name__ == "__main__":
    main()
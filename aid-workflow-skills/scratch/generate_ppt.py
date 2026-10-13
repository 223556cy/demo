"""
1+N 数字员工框架 Skill 自演进进展汇报
生成 PPT — 16:9 宽屏, 微软雅黑
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from copy import deepcopy
from lxml import etree

# ============== 配色 ==============
NAVY = RGBColor(0x0B, 0x2E, 0x59)        # 深蓝（主色）
BLUE = RGBColor(0x1E, 0x88, 0xE5)        # 中蓝
LIGHT_BLUE = RGBColor(0xE3, 0xF2, 0xFD)  # 浅蓝
RED = RGBColor(0xC0, 0x39, 0x2B)         # 强调红
ORANGE = RGBColor(0xE6, 0x5C, 0x00)      # 诊断-橙
GREEN = RGBColor(0x2E, 0x7D, 0x32)       # 通过-绿
PINK = RGBColor(0xAD, 0x14, 0x57)        # 裁判-粉
GRAY_DARK = RGBColor(0x42, 0x42, 0x42)   # 深灰
GRAY = RGBColor(0x75, 0x75, 0x75)        # 中灰
GRAY_LIGHT = RGBColor(0xF5, 0xF5, 0xF5)  # 浅灰背景
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0xFA, 0xFA, 0xFA)

CN_FONT = "微软雅黑"
EN_FONT = "Calibri"

# ============== 工具函数 ==============
def set_run_font(run, name=CN_FONT, size=14, bold=False, color=GRAY_DARK):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    # 中文字体设置（关键）
    rPr = run._r.get_or_add_rPr()
    # 删除已有的 eastAsia 标签
    for ea in rPr.findall(qn('a:ea')):
        rPr.remove(ea)
    ea = etree.SubElement(rPr, qn('a:ea'))
    ea.set('typeface', name)

def add_text_box(slide, left, top, width, height, text, font_size=14, bold=False,
                 color=GRAY_DARK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, font=CN_FONT):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, name=font, size=font_size, bold=bold, color=color)
    return tb

def add_filled_rect(slide, left, top, width, height, fill_color, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    # 调整圆角半径
    shape.adjustments[0] = 0.08
    shape.shadow.inherit = False
    return shape

def add_rect(slide, left, top, width, height, fill_color, line_color=None):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    if line_color:
        shape.line.color.rgb = line_color
        shape.line.width = Pt(1.5)
    else:
        shape.line.fill.background()
    shape.shadow.inherit = False
    return shape

def add_arrow(slide, left, top, width, height, color=GRAY):
    arrow = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, left, top, width, height)
    arrow.fill.solid()
    arrow.fill.fore_color.rgb = color
    arrow.line.fill.background()
    arrow.shadow.inherit = False
    return arrow

def add_line(slide, x1, y1, x2, y2, color=GRAY, weight=1.5):
    from pptx.util import Emu
    line = slide.shapes.add_connector(1, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line

def add_text_in_shape(shape, text, font_size=12, bold=False, color=GRAY_DARK, align=PP_ALIGN.CENTER):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(45720); tf.margin_right = Emu(45720)
    tf.margin_top = Emu(36000); tf.margin_bottom = Emu(36000)
    p = tf.paragraphs[0]
    p.alignment = align
    run = p.add_run()
    run.text = text
    set_run_font(run, size=font_size, bold=bold, color=color)
    return tf

def add_title_bar(slide, title_text, subtitle_text=None):
    # 顶部装饰条
    add_rect(slide, Inches(0), Inches(0), Inches(13.333), Inches(0.55), NAVY)
    # 标题
    add_text_box(slide, Inches(0.5), Inches(0.08), Inches(10), Inches(0.4),
                 title_text, font_size=20, bold=True, color=WHITE)
    if subtitle_text:
        add_text_box(slide, Inches(0.5), Inches(0.6), Inches(12), Inches(0.35),
                     subtitle_text, font_size=11, color=GRAY)
    # 右下角页脚
    add_text_box(slide, Inches(12.0), Inches(7.1), Inches(1.2), Inches(0.3),
                 "1+N 框架 · 内部汇报", font_size=9, color=GRAY,
                 align=PP_ALIGN.RIGHT)

def add_page_number(slide, num, total):
    add_text_box(slide, Inches(12.5), Inches(7.1), Inches(0.6), Inches(0.3),
                 f"{num} / {total}", font_size=9, color=GRAY, align=PP_ALIGN.RIGHT)

def add_table(slide, left, top, width, height, data, header_color=NAVY,
              header_text_color=WHITE, body_font_size=11, header_font_size=12,
              col_widths=None, row_heights=None):
    rows = len(data)
    cols = len(data[0])
    table_shape = slide.shapes.add_table(rows, cols, left, top, width, height)
    table = table_shape.table
    if col_widths:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w
    if row_heights:
        for i, h in enumerate(row_heights):
            table.rows[i].height = h
    for i, row in enumerate(data):
        for j, cell_text in enumerate(row):
            cell = table.cell(i, j)
            cell.fill.solid()
            if i == 0:
                cell.fill.fore_color.rgb = header_color
            else:
                cell.fill.fore_color.rgb = WHITE if i % 2 == 1 else GRAY_LIGHT
            cell.margin_left = Emu(72000); cell.margin_right = Emu(72000)
            cell.margin_top = Emu(36000); cell.margin_bottom = Emu(36000)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            tf.clear()
            p = tf.paragraphs[0]
            p.alignment = PP_ALIGN.LEFT if j > 0 else PP_ALIGN.CENTER
            run = p.add_run()
            run.text = str(cell_text)
            if i == 0:
                set_run_font(run, size=header_font_size, bold=True, color=header_text_color)
            else:
                set_run_font(run, size=body_font_size, color=GRAY_DARK)
    return table

# ============== 创建演示文稿 ==============
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

TOTAL_SLIDES = 12
blank_layout = prs.slide_layouts[6]

# ============== Slide 1: 封面 ==============
s1 = prs.slides.add_slide(blank_layout)
# 背景渐变效果（用色块）
add_rect(s1, Inches(0), Inches(0), Inches(13.333), Inches(7.5), NAVY)
add_rect(s1, Inches(0), Inches(5.5), Inches(13.333), Inches(2), BLUE)
# 装饰圆
add_filled_rect(s1, Inches(11.5), Inches(0.5), Inches(1.2), Inches(1.2), RED).adjustments[0] = 0.5
add_filled_rect(s1, Inches(0.5), Inches(6.0), Inches(0.6), Inches(0.6), WHITE).adjustments[0] = 0.5
# 主标题
add_text_box(s1, Inches(1), Inches(2.2), Inches(11), Inches(1.0),
             "1+N 数字员工框架", font_size=44, bold=True, color=WHITE)
add_text_box(s1, Inches(1), Inches(3.2), Inches(11), Inches(1.0),
             "Skill 自演进进展汇报", font_size=36, bold=True, color=WHITE)
# 副标题
add_text_box(s1, Inches(1), Inches(4.5), Inches(11), Inches(0.5),
             "v3 PR 闭环模式  ·  rev-01 v2 真实测试  ·  5 项关键修复",
             font_size=16, color=LIGHT_BLUE)
# 底部信息
add_text_box(s1, Inches(1), Inches(6.3), Inches(11), Inches(0.4),
             "汇报人：1+N 框架团队        日期：2026-07-08",
             font_size=14, color=WHITE)
add_text_box(s1, Inches(1), Inches(6.7), Inches(11), Inches(0.4),
             "项目目录：D:/huawei/Demo/",
             font_size=12, color=LIGHT_BLUE)

# ============== Slide 2: 目录 ==============
s2 = prs.slides.add_slide(blank_layout)
add_title_bar(s2, "目录 / Agenda")
add_page_number(s2, 2, TOTAL_SLIDES)
toc_items = [
    ("01", "汇报摘要", "本季度 Skill 自演进关键成果一览"),
    ("02", "1+N 团队全景", "5 个数字员工角色与职责分工"),
    ("03", "进展一：四阶闭环 v3", "Skill 修改从单向变闭环"),
    ("04", "进展二：dev-02 沙箱回归", "用真实制品量化 Skill 改动有效性"),
    ("05", "进展三：rev-01 v2 升级", "审查员从「看报告」到「亲手测」"),
    ("06", "进展四：基础设施修复", "2026-07-07 同日完成的 5 项关键修复"),
    ("07", "框架总览图", "v3 PR 闭环模式全景"),
    ("08", "关键设计决策 & 下一步", "为何不采用 SkillOpt 框架 / 后续计划"),
]
top = 1.4
for i, (num, title, desc) in enumerate(toc_items):
    y = Inches(top + i * 0.65)
    # 序号方块
    add_rect(s2, Inches(1.0), y, Inches(0.7), Inches(0.5), NAVY)
    add_text_in_shape(add_rect(s2, Inches(1.0), y, Inches(0.7), Inches(0.5), NAVY),
                      num, font_size=18, bold=True, color=WHITE)
    # 标题
    add_text_box(s2, Inches(1.9), y + Inches(0.02), Inches(4.0), Inches(0.45),
                 title, font_size=16, bold=True, color=NAVY)
    # 描述
    add_text_box(s2, Inches(5.9), y + Inches(0.05), Inches(7.0), Inches(0.45),
                 desc, font_size=12, color=GRAY)

# ============== Slide 3: 汇报摘要 ==============
s3 = prs.slides.add_slide(blank_layout)
add_title_bar(s3, "01  汇报摘要", "Skill 自演进从单向修改升级为四阶闭环 + 真实 UI 测试")
add_page_number(s3, 3, TOTAL_SLIDES)

# 核心成果卡片
card_w = Inches(3.0); card_h = Inches(2.0); gap = Inches(0.25)
card_x_start = Inches(0.7); card_y = Inches(1.5)
cards = [
    ("四阶闭环", "v3 PR 模式", "分析 → 修改\n→ 回归 → 裁判", NAVY),
    ("沙箱回归", "dev-02 体系", "复用 1+N agent\n跑 12 个历史 issue", BLUE),
    ("真实测试", "rev-01 v2", "亲手跑 UI\n+ 8 张截图 + 3 dump", ORANGE),
    ("5 项修复", "P0/P1 闭环", "SOUL 注入 / 超时\n/ NameError / judge", RED),
]
for i, (title, sub, body, color) in enumerate(cards):
    x = card_x_start + (card_w + gap) * i
    # 顶部色条
    add_rect(s3, x, card_y, card_w, Inches(0.4), color)
    add_text_in_shape(add_rect(s3, x, card_y, card_w, Inches(0.4), color),
                      title, font_size=14, bold=True, color=WHITE)
    # 主体
    add_filled_rect(s3, x, card_y + Inches(0.4), card_w, card_h - Inches(0.4), WHITE, color)
    add_text_box(s3, x + Inches(0.2), card_y + Inches(0.5), card_w - Inches(0.4), Inches(0.4),
                 sub, font_size=14, bold=True, color=color)
    add_text_box(s3, x + Inches(0.2), card_y + Inches(0.95), card_w - Inches(0.4), Inches(1.0),
                 body, font_size=13, color=GRAY_DARK)

# 下方价值陈述
value_y = Inches(4.0)
add_rect(s3, Inches(0.7), value_y, Inches(11.93), Inches(2.5), GRAY_LIGHT)
add_text_box(s3, Inches(0.9), value_y + Inches(0.15), Inches(11.5), Inches(0.4),
             "🎯 核心价值", font_size=15, bold=True, color=NAVY)
value_points = [
    "•  Skill 改动第一次有了「有效 vs 无效」的可量化裁判",
    "•  dev-01 提交的代码必须保证在 DevEco 模拟器上真的能跑通",
    "•  所有角色都是真实 agent —— 可监控、可查询、可审计、可回滚",
    "•  拒绝 SkillOpt 框架：1+N 体系本身就是「人驱动的 SkillOpt」",
]
for i, p in enumerate(value_points):
    add_text_box(s3, Inches(0.9), value_y + Inches(0.6 + i * 0.4), Inches(11.5), Inches(0.4),
                 p, font_size=13, color=GRAY_DARK)

# ============== Slide 4: 1+N 团队全景 ==============
s4 = prs.slides.add_slide(blank_layout)
add_title_bar(s4, "02  1+N 团队全景", "5 个数字员工 + 独立 Hermes 进程 + 单一 SOUL 真理源")
add_page_number(s4, 4, TOTAL_SLIDES)

# 团队表
team_data = [
    ["角色", "GitHub 账号", "Gateway 端口", "核心职责"],
    ["dev-01", "littleleafccccc", "8100", "执行 AID-Workflow（PLANNING→IMPLEMENTING→APPLYING）"],
    ["rev-01", "littleleafbbbbb", "8101", "v2 起：亲手跑 UI 测试 + 构造补充用例 + 截图取证"],
    ["skillopt-01", "littleleafOptimizer", "8104", "根据 analysis 反馈修改 aid-workflow-skills"],
    ["analysis", "（内部账号）", "—", "闭环裁判：诊断 Skill 问题 + 判定回归结果"],
    ["dev-02", "littleleafaaaaa", "8105", "沙箱回归：用新 Skill 跑 12 个历史 issue"],
]
add_table(s4, Inches(0.5), Inches(1.4), Inches(12.3), Inches(2.8), team_data,
          col_widths=[Inches(1.6), Inches(2.3), Inches(1.4), Inches(7.0)],
          body_font_size=12, header_font_size=13)

# AID-Workflow 4 阶段
aw_y = Inches(4.5)
add_text_box(s4, Inches(0.5), aw_y, Inches(12), Inches(0.4),
             "📋 AID-Workflow 四阶段执行流", font_size=15, bold=True, color=NAVY)
aw_stages = [
    ("PLANNING", "产出 proposal / spec / design", LIGHT_BLUE, NAVY),
    ("IMPLEMENTING", "任务分解为 tasks.md", LIGHT_BLUE, NAVY),
    ("APPLYING", "TDD 编码 + 编译 + 测试", ORANGE, WHITE),
    ("ARCHIVE", "归档到 specs/archives/", LIGHT_BLUE, NAVY),
]
sw = Inches(2.9); sh = Inches(1.0); sx = Inches(0.5); sy = Inches(5.0)
for i, (stage, desc, bg, fg) in enumerate(aw_stages):
    x = sx + (sw + Inches(0.15)) * i
    add_filled_rect(s4, x, sy, sw, sh, bg, NAVY)
    add_text_box(s4, x + Inches(0.1), sy + Inches(0.08), sw - Inches(0.2), Inches(0.4),
                 stage, font_size=14, bold=True, color=fg, align=PP_ALIGN.CENTER)
    add_text_box(s4, x + Inches(0.1), sy + Inches(0.5), sw - Inches(0.2), Inches(0.5),
                 desc, font_size=11, color=GRAY_DARK, align=PP_ALIGN.CENTER)
    # 箭头
    if i < 3:
        add_arrow(s4, x + sw - Inches(0.05), sy + Inches(0.35),
                  Inches(0.2), Inches(0.3), NAVY)

# 铁律
add_text_box(s4, Inches(0.5), Inches(6.2), Inches(12), Inches(0.4),
             "⚖️  内置 4 条铁律：build_hap.bat | TDD 不可跳 | UI 必跑 harmonyos-ui-test | apply-report 数据必须真实",
             font_size=11, color=GRAY, align=PP_ALIGN.LEFT)

# ============== Slide 5: 进展一导览 ==============
s5 = prs.slides.add_slide(blank_layout)
add_title_bar(s5, "03  进展一：四阶闭环 v3", "Skill 修改从单向链升级为「分析 → 修改 → 回归 → 裁判」")
add_page_number(s5, 5, TOTAL_SLIDES)

# 核心循环图（4 个阶段横向排列）
stage_w = Inches(2.7); stage_h = Inches(2.4); gap = Inches(0.4)
total_w = stage_w * 4 + gap * 3
sx0 = (Inches(13.333) - total_w) / 2
sy = Inches(1.5)
stages = [
    ("① 诊断", "analysis", "读 session + spec\n+ rev-01 意见", "输出 diagnosis.json\n+ label: skillopt:pending", ORANGE),
    ("② 修改", "skillopt-01", "改 aid-workflow-skills\n开分支", "commit + 分支\n+ [regression] issue", BLUE),
    ("③ 回归", "dev-02", "拉新 skill\n跑完整 AID-Workflow", "新 spec/代码/测试\n+ regression-done", GREEN),
    ("④ 裁判", "analysis", "对比新旧制品\n判定有效性", "[approved] / [rejected]\n不转回 skillopt-01", PINK),
]
for i, (stage, agent, action, output, color) in enumerate(stages):
    x = sx0 + (stage_w + gap) * i
    # 阶段标题
    add_filled_rect(s5, x, sy, stage_w, Inches(0.6), color)
    add_text_box(s5, x + Inches(0.1), sy + Inches(0.05), stage_w - Inches(0.2), Inches(0.3),
                 stage, font_size=18, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
    add_text_box(s5, x + Inches(0.1), sy + Inches(0.32), stage_w - Inches(0.2), Inches(0.25),
                 f"by {agent}", font_size=10, color=WHITE, align=PP_ALIGN.CENTER)
    # 主体
    add_filled_rect(s5, x, sy + Inches(0.6), stage_w, stage_h - Inches(0.6), WHITE, color)
    add_text_box(s5, x + Inches(0.15), sy + Inches(0.7), stage_w - Inches(0.3), Inches(0.25),
                 "动作", font_size=10, bold=True, color=color)
    add_text_box(s5, x + Inches(0.15), sy + Inches(0.95), stage_w - Inches(0.3), Inches(0.7),
                 action, font_size=11, color=GRAY_DARK)
    add_text_box(s5, x + Inches(0.15), sy + Inches(1.65), stage_w - Inches(0.3), Inches(0.25),
                 "输出", font_size=10, bold=True, color=color)
    add_text_box(s5, x + Inches(0.15), sy + Inches(1.9), stage_w - Inches(0.3), Inches(0.5),
                 output, font_size=10, color=GRAY_DARK)
    # 箭头
    if i < 3:
        ax = x + stage_w + Inches(0.05)
        add_arrow(s5, ax, sy + Inches(1.1), Inches(0.3), Inches(0.3), NAVY)

# REJECTED 反馈路径
reject_y = Inches(4.4)
add_text_box(s5, Inches(0.5), reject_y, Inches(12.3), Inches(0.4),
             "↩️  REJECTED 路径：裁判 → 打回 ② skillopt-01 重新修改（不触发 analysis，避免死循环）",
             font_size=12, color=RED, align=PP_ALIGN.CENTER)

# 关键价值
val_y = Inches(5.1)
add_rect(s5, Inches(0.5), val_y, Inches(12.3), Inches(2.0), GRAY_LIGHT)
add_text_box(s5, Inches(0.7), val_y + Inches(0.1), Inches(12), Inches(0.4),
             "🎯 关键价值", font_size=14, bold=True, color=NAVY)
add_text_box(s5, Inches(0.7), val_y + Inches(0.5), Inches(12), Inches(1.5),
             "•  Skill 改动第一次有了「有效 vs 无效」的可量化裁判\n"
             "•  analysis 在 dev-02 路径上不再触发 skillopt-01，避免 skillopt → dev-02 → analysis → skillopt 死循环\n"
             "•  从「人改 Skill 试试看」变成「Skill 改动必须通过真实制品验证才生效」",
             font_size=12, color=GRAY_DARK)

# ============== Slide 6: 进展二 dev-02 沙箱回归 ==============
s6 = prs.slides.add_slide(blank_layout)
add_title_bar(s6, "04  进展二：dev-02 沙箱回归", "复用 1+N 既有 agent 体系，开辟独立的回归沙箱")
add_page_number(s6, 6, TOTAL_SLIDES)

# 左侧：架构对比
left_x = Inches(0.5); left_y = Inches(1.4)
add_text_box(s6, left_x, left_y, Inches(6), Inches(0.4),
             "🆚 架构决策对比", font_size=15, bold=True, color=NAVY)
compare_data = [
    ["维度", "传统 CI 方案", "本框架方案（dev-02）"],
    ["基础设施", "新开 GitHub Action runner", "复用 1+N 既有 agent"],
    ["运行环境", "Docker 容器 / VM", "dev-02 独立 Hermes profile"],
    ["可监控性", "看 CI 日志", "实时查询 agent 状态"],
    ["故障诊断", "log diff", "agent 反向推理 + 历史制品对比"],
    ["Skill 源", "直接 commit 触发", "拉 aid-workflow-skills 分支"],
    ["维护成本", "runner 进程要保活", "无机器依赖，cron 触发"],
]
add_table(s6, left_x, left_y + Inches(0.5), Inches(6.0), Inches(2.8), compare_data,
          col_widths=[Inches(1.3), Inches(2.2), Inches(2.5)],
          body_font_size=10, header_font_size=11)

# 左侧下半：12 issue 回归集
reg_y = Inches(4.4)
add_text_box(s6, left_x, reg_y, Inches(6), Inches(0.4),
             "📊 12 issue 回归集", font_size=14, bold=True, color=NAVY)
add_rect(s6, left_x, reg_y + Inches(0.45), Inches(6.0), Inches(2.3), GRAY_LIGHT)
reg_text = [
    "•  语料来源：worktrees/issue-N/ + specs/changes/",
    "•  覆盖 10 个已完成需求（含 real-time-preview / QR share / unit conversion 等）",
    "•  每个 issue 含：proposal / design / tasks / apply-report + 真实代码",
    "•  回归产出：新 spec + 真实代码 + 测试报告（与历史制品逐项对比）",
    "•  量化指标：compile_rate / test_rate / ui_rate",
]
for i, p in enumerate(reg_text):
    add_text_box(s6, left_x + Inches(0.15), reg_y + Inches(0.6 + i * 0.4),
                 Inches(5.7), Inches(0.4), p, font_size=11, color=GRAY_DARK)

# 右侧：dev-02 触发流程
right_x = Inches(7.0); right_y = Inches(1.4)
add_text_box(s6, right_x, right_y, Inches(6), Inches(0.4),
             "🔁 dev-02 触发流程", font_size=15, bold=True, color=NAVY)
flow_steps = [
    "1.  skillopt-01 合并 PR 到 aid-workflow-skills",
    "2.  创建 [regression] issue 分配给 dev-02",
    "3.  dev-02 cron (10min) 拉取最新 skill",
    "4.  跑完整 AID-Workflow（重跑原 issue）",
    "5.  产出报告 + label: regression-done",
    "6.  转交 analysis 裁判",
    "7.  analysis → [approved] / [rejected]",
]
for i, step in enumerate(flow_steps):
    y = right_y + Inches(0.5 + i * 0.45)
    # 序号圆
    dot = add_filled_rect(s6, right_x, y, Inches(0.35), Inches(0.35), GREEN)
    dot.adjustments[0] = 0.5
    add_text_in_shape(dot, str(i+1), font_size=12, bold=True, color=WHITE)
    add_text_box(s6, right_x + Inches(0.5), y + Inches(0.05), Inches(5.3), Inches(0.4),
                 step, font_size=12, color=GRAY_DARK)
    if i < len(flow_steps) - 1:
        add_line(s6, right_x + Inches(0.175) + 4572000, y + Inches(0.35),
                 right_x + Inches(0.175) + 4572000, y + Inches(0.45),
                 color=GRAY, weight=1)

# 右侧下半：隔离保证
iso_y = Inches(5.0)
add_text_box(s6, right_x, iso_y, Inches(6), Inches(0.4),
             "🔒 隔离保证", font_size=14, bold=True, color=NAVY)
add_rect(s6, right_x, iso_y + Inches(0.4), Inches(6.0), Inches(1.7), GRAY_LIGHT)
iso_items = [
    "•  Skill 源隔离：dev-02 拉 aid-workflow-skills，dev-01 用 calculatorHuawei/.claude/skills/",
    "•  身份隔离：dev-02 用新 GitHub PAT（littleleafaaaaa）",
    "•  进程隔离：独立 Hermes profile + Gateway port 8105",
    "•  SOUL 隔离：dev-02-SOUL.md 明确角色为「regression runner」",
]
for i, p in enumerate(iso_items):
    add_text_box(s6, right_x + Inches(0.15), iso_y + Inches(0.5 + i * 0.35),
                 Inches(5.7), Inches(0.4), p, font_size=11, color=GRAY_DARK)

# ============== Slide 7: 进展三 rev-01 v2 升级 ==============
s7 = prs.slides.add_slide(blank_layout)
add_title_bar(s7, "05  进展三：rev-01 v2 升级", "审查员从「看 dev-01 报告」升级为「亲手跑 UI + 截图取证」")
add_page_number(s7, 7, TOTAL_SLIDES)

# v1 vs v2 对比表
add_text_box(s7, Inches(0.5), Inches(1.3), Inches(12), Inches(0.4),
             "🆚 v1 vs v2 能力对比", font_size=15, bold=True, color=NAVY)
v_data = [
    ["维度", "v1（改动前）", "v2（当前）"],
    ["SOUL.md", "15 行默认模板", "162 行，含 5 阶段工作流"],
    ["UI 测试", "只看 dev-01 的测试报告", "亲手跑 harmonyos-ui-test skill + DevEco 模拟器"],
    ["测试用例", "只跑 dev-01 写的用例", "自构造 ≥ 8 个补充用例（边界/异常/状态/可访问性）"],
    ["截图", "复用 dev-01 的截图", "自己重跑 ≥ 8 张截图，命名 issue-N-step-<seq>-<state>-<ts>.png"],
    ["uiautomator dump", "看 dev-01 的 dump", "自己 dump ≥ 3 份不同页面状态"],
    ["模拟器不可用", "直接跳过", "attempt ≥ 3 次后才标 skipped（铁律 7）"],
    ["审查输出", "verdict + blocking", "JSON 含 ui_test_evidence 字段（test_cases_authored / passed / failed / screenshots）"],
]
add_table(s7, Inches(0.5), Inches(1.75), Inches(12.3), Inches(3.2), v_data,
          col_widths=[Inches(2.2), Inches(4.5), Inches(5.6)],
          body_font_size=11, header_font_size=12)

# 5 阶段工作流
wf_y = Inches(5.1)
add_text_box(s7, Inches(0.5), wf_y, Inches(12), Inches(0.4),
             "📋 5 阶段工作流", font_size=14, bold=True, color=NAVY)
wf_steps = [
    ("1", "读产物", "5 min"),
    ("2", "构造补充用例", "10 min"),
    ("3", "亲手跑 UI", "15-30 min"),
    ("4", "对比制品", "5 min"),
    ("5", "写 verdict", "5 min"),
]
wsw = Inches(2.3); wsh = Inches(0.85); wsx = Inches(0.5); wsy = Inches(5.55)
for i, (num, name, dur) in enumerate(wf_steps):
    x = wsx + (wsw + Inches(0.1)) * i
    add_filled_rect(s7, x, wsy, wsw, wsh, WHITE, ORANGE)
    add_text_in_shape(add_filled_rect(s7, x, wsy, wsw, Inches(0.3), ORANGE),
                      f"阶段 {num}", font_size=10, bold=True, color=WHITE)
    add_text_box(s7, x + Inches(0.1), wsy + Inches(0.32), wsw - Inches(0.2), Inches(0.3),
                 name, font_size=12, bold=True, color=GRAY_DARK, align=PP_ALIGN.CENTER)
    add_text_box(s7, x + Inches(0.1), wsy + Inches(0.55), wsw - Inches(0.2), Inches(0.3),
                 dur, font_size=10, color=GRAY, align=PP_ALIGN.CENTER)
    if i < 4:
        add_arrow(s7, x + wsw - Inches(0.05), wsy + Inches(0.35),
                  Inches(0.15), Inches(0.2), NAVY)

# 硬规则
hr_y = Inches(6.55)
add_text_box(s7, Inches(0.5), hr_y, Inches(12.3), Inches(0.4),
             "🚫 硬规则：不准复用截图 / 不准跳过补充用例 / 不准伪造 UI 日志 / attempt≥3 次后才标 skipped",
             font_size=11, color=RED)

# ============== Slide 8: 进展四 基础设施修复 ==============
s8 = prs.slides.add_slide(blank_layout)
add_title_bar(s8, "06  进展四：基础设施关键修复", "2026-07-07 同日完成 5 项 P0/P1 修复，让闭环真正能跑通")
add_page_number(s8, 8, TOTAL_SLIDES)

fix_data = [
    ["#", "修复", "现象", "根因", "修复要点"],
    ["P0", "SOUL.md 注入", "改 SOUL.md 不生效",
     "4 个 dispatcher 没把 SOUL 注入 system prompt",
     "claude --append-system-prompt + load_soul()"],
    ["P0", "skillopt-01 超时", "dispatch 一直 error",
     "subprocess.run(timeout=600) 阻塞 10min 超过 cron 120s",
     "Popen 非阻塞 + 3 状态机 + MAX_ISSUES=1"],
    ["P0", "dev-02 漏配", "issue #34 跑两次都阻塞",
     "v8 模板没应用到 dev-02（最新加入闭环，被漏）",
     "镜像 dev-01 模板：SOUL + SDK env + Popen"],
    ["P0", "analysis judge 3 bug", "verdict 永远 UNKNOWN",
     "① comments 顺序 ② verdict 兜底源 ③ labels 未透传",
     "倒序取最新 + verdict 读 diagnosis.json + labels 透传"],
    ["P1", "finalize NameError", "finalize 连续 4 次失败",
     "build_diagnosis_comment L853 笔误 data → diagnosis",
     "1 行修复：data → diagnosis"],
]
add_table(s8, Inches(0.4), Inches(1.4), Inches(12.5), Inches(3.5), fix_data,
          col_widths=[Inches(0.7), Inches(2.1), Inches(2.2), Inches(3.8), Inches(3.7)],
          body_font_size=10, header_font_size=12)

# 底部：核心收益
ben_y = Inches(5.2)
add_rect(s8, Inches(0.4), ben_y, Inches(12.5), Inches(1.9), GRAY_LIGHT)
add_text_box(s8, Inches(0.6), ben_y + Inches(0.1), Inches(12), Inches(0.4),
             "💡 修复带来的能力提升", font_size=14, bold=True, color=NAVY)
ben_items = [
    "•  改 SOUL.md 真的生效：dispatch 链路全部接上 --append-system-prompt",
    "•  skillopt-01 不再 timeout：Popen 非阻塞 + 状态机让 cron 稳定触发",
    "•  dev-02 真的能跑通：issue #34 产出 BUILD SUCCESSFUL + 7/7 Node + 5/5 UI 测试",
    "•  analysis 闭环正确：regression-done 路径给 [approved] verdict，不再误转 skillopt-01",
]
for i, p in enumerate(ben_items):
    add_text_box(s8, Inches(0.6), ben_y + Inches(0.5 + i * 0.32),
                 Inches(12), Inches(0.35), p, font_size=11, color=GRAY_DARK)

# ============== Slide 9: 框架总览图 ==============
s9 = prs.slides.add_slide(blank_layout)
add_title_bar(s9, "07  框架总览图", "v3 PR 闭环模式全景（从触发到生效）")
add_page_number(s9, 9, TOTAL_SLIDES)

# 大圆环流程图
# 中心：闭环
center_x = Inches(6.667); center_y = Inches(4.2)
add_filled_rect(s9, center_x - Inches(1.4), center_y - Inches(0.7),
                Inches(2.8), Inches(1.4), NAVY).adjustments[0] = 0.3
add_text_in_shape(add_filled_rect(s9, center_x - Inches(1.4), center_y - Inches(0.7),
                                   Inches(2.8), Inches(1.4), NAVY),
                  "Skill 自演化\n四阶闭环 v3", font_size=15, bold=True, color=WHITE)

# 四个角：4 个阶段
# 左上：分析
nw_x, nw_y = Inches(1.2), Inches(1.6)
add_filled_rect(s9, nw_x, nw_y, Inches(3.0), Inches(1.6), ORANGE).adjustments[0] = 0.15
tf = s9.shapes[-1].text_frame
tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "① analysis 诊断"
set_run_font(r1, size=14, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "读 session + spec + rev-01 意见"
set_run_font(r2, size=10, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "→ diagnosis.json"
set_run_font(r3, size=10, bold=True, color=WHITE)

# 右上：skillopt-01
ne_x, ne_y = Inches(9.1), Inches(1.6)
add_filled_rect(s9, ne_x, ne_y, Inches(3.0), Inches(1.6), BLUE).adjustments[0] = 0.15
tf = s9.shapes[-1].text_frame
tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "② skillopt-01 改 skill"
set_run_font(r1, size=14, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "改 aid-workflow-skills"
set_run_font(r2, size=10, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "→ commit + 分支 + [regression] issue"
set_run_font(r3, size=10, bold=True, color=WHITE)

# 左下：dev-02
sw_x, sw_y = Inches(1.2), Inches(5.0)
add_filled_rect(s9, sw_x, sw_y, Inches(3.0), Inches(1.6), GREEN).adjustments[0] = 0.15
tf = s9.shapes[-1].text_frame
tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "③ dev-02 沙箱回归"
set_run_font(r1, size=14, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "拉新 skill + 跑完整 AID-Workflow"
set_run_font(r2, size=10, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "→ 新制品 + regression-done"
set_run_font(r3, size=10, bold=True, color=WHITE)

# 右下：analysis 裁判
se_x, se_y = Inches(9.1), Inches(5.0)
add_filled_rect(s9, se_x, se_y, Inches(3.0), Inches(1.6), PINK).adjustments[0] = 0.15
tf = s9.shapes[-1].text_frame
tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "④ analysis 裁判"
set_run_font(r1, size=14, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "对比新旧制品"
set_run_font(r2, size=10, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "→ [approved] / [rejected]"
set_run_font(r3, size=10, bold=True, color=WHITE)

# 箭头：① → ② （顶部）
arrow1 = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.3), Inches(2.2),
                              Inches(4.5), Inches(0.3))
arrow1.fill.solid(); arrow1.fill.fore_color.rgb = NAVY
arrow1.line.fill.background(); arrow1.shadow.inherit = False

# ② → ③ （右侧下行 → 左下）
# 用弯箭头：从右上到左下，拆成 2 段
arrow2 = s9.shapes.add_shape(MSO_SHAPE.DOWN_ARROW, Inches(10.4), Inches(3.4),
                              Inches(0.3), Inches(1.4))
arrow2.fill.solid(); arrow2.fill.fore_color.rgb = NAVY
arrow2.line.fill.background(); arrow2.shadow.inherit = False

# ③ → ④ （底部，从左到右）
arrow3 = s9.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(4.3), Inches(5.65),
                              Inches(4.5), Inches(0.3))
arrow3.fill.solid(); arrow3.fill.fore_color.rgb = NAVY
arrow3.line.fill.background(); arrow3.shadow.inherit = False

# ④ → ① （左侧上行，用虚线表示 REJECTED 反向路径）
# 从左下到左上，拆为向上箭头
arrow4 = s9.shapes.add_shape(MSO_SHAPE.UP_ARROW, Inches(2.5), Inches(3.4),
                              Inches(0.3), Inches(1.4))
arrow4.fill.solid(); arrow4.fill.fore_color.rgb = RED
arrow4.line.fill.background(); arrow4.shadow.inherit = False
# 在向上箭头旁加 "REJECTED" 标签
add_text_box(s9, Inches(1.5), Inches(3.9), Inches(1.0), Inches(0.4),
             "REJECTED", font_size=10, bold=True, color=RED, align=PP_ALIGN.CENTER)

# 中心到四角的虚线（标识归属）
# 略，保持简洁

# 底部说明
add_text_box(s9, Inches(0.5), Inches(6.8), Inches(12.3), Inches(0.4),
             "🟢 实线箭头 = 正向流转（成功路径）  ·  🔴 红色箭头 = REJECTED 反向路径（打回 skillopt-01 重做）",
             font_size=11, color=GRAY_DARK, align=PP_ALIGN.CENTER)

# ============== Slide 10: 关键设计决策 ==============
s10 = prs.slides.add_slide(blank_layout)
add_title_bar(s10, "08  关键设计决策", "为何这样设计？4 个备查要点")
add_page_number(s10, 10, TOTAL_SLIDES)

decisions = [
    ("①", "不采用 SkillOpt 框架",
     "microsoft/SkillOpt 是 LLM 训练循环框架。我们已有 1+N 体系（3 agent + skillopt-01）本质就是「人驱动的 SkillOpt」—— 慢但可解释、多视角交叉验证、与生产端同栈零迁移成本。",
     "→ 维持 1+N 现状，按 v3 PR 闭环迭代", NAVY),
    ("②", "dev-02 复用 1+N 基础设施",
     "新开 GitHub Action runner 需要保活进程、维护 runner 镜像；复用现有 agent 体系 = 可监控、可查询、可调试，与 dev-01 同栈同 SOUL 模板。",
     "→ 独立 Hermes profile + 独立 PAT", BLUE),
    ("③", "Skill 源严格隔离",
     "dev-02 必须从 aid-workflow-skills 仓拉取测试 skill，不能复用 dev-01 的生产 skill (calculatorHuawei/.claude/skills/)。",
     "→ 防止测试污染生产", GREEN),
    ("④", "analysis 闭环不再回转 skillopt-01",
     "如果 analysis 在 dev-02 回归后把 REQUEST_CHANGES 转回 skillopt-01，会形成 skillopt → dev-02 → analysis → skillopt 死循环。",
     "→ 闭环裁判只给 verdict，由人决定是否再开 PR", ORANGE),
]
y = 1.4
for num, title, body, footer, color in decisions:
    # 左侧色块
    add_rect(s10, Inches(0.5), Inches(y), Inches(0.7), Inches(1.25), color)
    add_text_in_shape(add_rect(s10, Inches(0.5), Inches(y), Inches(0.7), Inches(1.25), color),
                      num, font_size=28, bold=True, color=WHITE)
    # 标题
    add_text_box(s10, Inches(1.4), Inches(y), Inches(11.5), Inches(0.4),
                 title, font_size=15, bold=True, color=color)
    # 正文
    add_text_box(s10, Inches(1.4), Inches(y + 0.4), Inches(11.5), Inches(0.55),
                 body, font_size=11, color=GRAY_DARK)
    # 决定
    add_text_box(s10, Inches(1.4), Inches(y + 0.95), Inches(11.5), Inches(0.3),
                 footer, font_size=11, bold=True, color=color)
    y += 1.35

# ============== Slide 11: 下一步计划 ==============
s11 = prs.slides.add_slide(blank_layout)
add_title_bar(s11, "09  下一步计划", "短期验证 + 中期基线 + 长期治理")
add_page_number(s11, 11, TOTAL_SLIDES)

# 时间线
phases = [
    ("短期（1-2 周）", "跑通首个完整 v3 闭环", [
        "•  issue #34 走完 analysis → skillopt → dev-02 → analysis 裁判",
        "•  验证 analysis 闭环只 judge、不转回 skillopt-01",
        "•  监控 4 dispatcher × 10min 频率的 cron 稳定性",
    ], RED),
    ("中期（1 个月）", "采集 12 issue 回归基线", [
        "•  compile_rate / test_rate / ui_rate 三个量化指标",
        "•  与历史制品逐项对比，建立「通过/失败」分类标准",
        "•  输出第一份基线报告，作为后续 Skill 改动的判据",
    ], ORANGE),
    ("长期（季度）", "推进 SOUL 单一真理源 + 治理", [
        "•  所有 dispatcher 统一读 agents/<agent>-SOUL.md",
        "•  推进 Skill 改动审计日志（每次改动的 diagnosis + verdict 留痕）",
        "•  将闭环流程固化到 AID-Workflow 的 aid-planning skill 中",
    ], GREEN),
]
y = 1.4
for label, title, items, color in phases:
    # 左侧色条
    add_rect(s11, Inches(0.5), Inches(y), Inches(0.3), Inches(1.7), color)
    # 阶段标签
    add_text_box(s11, Inches(1.0), Inches(y), Inches(2.5), Inches(0.4),
                 label, font_size=13, bold=True, color=color)
    # 标题
    add_text_box(s11, Inches(1.0), Inches(y + 0.4), Inches(11.5), Inches(0.4),
                 title, font_size=14, bold=True, color=NAVY)
    # 子项
    for i, item in enumerate(items):
        add_text_box(s11, Inches(1.0), Inches(y + 0.85 + i * 0.27), Inches(11.5), Inches(0.3),
                     item, font_size=11, color=GRAY_DARK)
    y += 1.8

# ============== Slide 12: 总结 / Q&A ==============
s12 = prs.slides.add_slide(blank_layout)
add_rect(s12, Inches(0), Inches(0), Inches(13.333), Inches(7.5), NAVY)
add_rect(s12, Inches(0), Inches(6.5), Inches(13.333), Inches(1), BLUE)
# 装饰圆
add_filled_rect(s12, Inches(11.0), Inches(0.5), Inches(1.5), Inches(1.5), RED).adjustments[0] = 0.5
add_filled_rect(s12, Inches(0.8), Inches(0.6), Inches(0.8), Inches(0.8), ORANGE).adjustments[0] = 0.5

# 大标题
add_text_box(s12, Inches(0.8), Inches(2.0), Inches(11.7), Inches(1.0),
             "Skill 自演进闭环 = 让 1+N 框架自我进化", font_size=36, bold=True, color=WHITE)
add_text_box(s12, Inches(0.8), Inches(3.1), Inches(11.7), Inches(0.6),
             "从「人改 Skill 试试看」到「Skill 改动必须通过真实制品验证才生效」",
             font_size=18, color=LIGHT_BLUE)

# 三句话总结
summaries = [
    "✅  v3 PR 闭环已落地：分析 → 修改 → 回归 → 裁判",
    "✅  rev-01 v2 已上线：真实 UI 测试 + 截图取证",
    "✅  5 项基础设施修复已完成：闭环可执行",
]
for i, p in enumerate(summaries):
    add_text_box(s12, Inches(0.8), Inches(4.2 + i * 0.5), Inches(11.7), Inches(0.4),
                 p, font_size=16, color=WHITE)

# Q&A
add_text_box(s12, Inches(0.8), Inches(6.0), Inches(11.7), Inches(0.5),
             "Q & A", font_size=22, bold=True, color=WHITE, align=PP_ALIGN.CENTER)
add_text_box(s12, Inches(0.8), Inches(6.65), Inches(11.7), Inches(0.4),
             "感谢聆听 · 1+N 框架团队 · D:/huawei/Demo/",
             font_size=12, color=LIGHT_BLUE, align=PP_ALIGN.CENTER)

# ============== 保存 ==============
output_path = "D:/huawei/Demo/_upload_target/1plusn-skill-evolution-2026-07-08.pptx"
prs.save(output_path)
import sys
sys.stdout.reconfigure(encoding='utf-8')
print(f"[OK] PPT saved: {output_path}")
print(f"     slides: {len(prs.slides)}")

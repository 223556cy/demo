"""
1+N 数字员工框架 — Skill 自演进进展
单页 PPT（16:9 一张搞定）
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

# 配色
NAVY = RGBColor(0x0B, 0x2E, 0x59)
BLUE = RGBColor(0x1E, 0x88, 0xE5)
LIGHT_BLUE = RGBColor(0xE3, 0xF2, 0xFD)
RED = RGBColor(0xC0, 0x39, 0x2B)
ORANGE = RGBColor(0xE6, 0x5C, 0x00)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
PINK = RGBColor(0xAD, 0x14, 0x57)
GRAY_DARK = RGBColor(0x33, 0x33, 0x33)
GRAY = RGBColor(0x75, 0x75, 0x75)
GRAY_LIGHT = RGBColor(0xF5, 0xF5, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
BG = RGBColor(0xFA, 0xFC, 0xFF)
CN = "微软雅黑"

def set_font(run, name=CN, size=12, bold=False, color=GRAY_DARK):
    run.font.name = name
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.color.rgb = color
    rPr = run._r.get_or_add_rPr()
    for ea in rPr.findall(qn('a:ea')):
        rPr.remove(ea)
    ea = etree.SubElement(rPr, qn('a:ea'))
    ea.set('typeface', name)

def add_text(slide, l, t, w, h, text, size=12, bold=False, color=GRAY_DARK,
             align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = Emu(0); tf.margin_right = Emu(0)
    tf.margin_top = Emu(0); tf.margin_bottom = Emu(0)
    p = tf.paragraphs[0]
    p.alignment = align
    r = p.add_run(); r.text = text
    set_font(r, size=size, bold=bold, color=color)
    return tb

def add_rect(slide, l, t, w, h, fill, line=None, radius=0.08):
    s = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, l, t, w, h)
    s.fill.solid(); s.fill.fore_color.rgb = fill
    if line:
        s.line.color.rgb = line; s.line.width = Pt(1.5)
    else:
        s.line.fill.background()
    s.adjustments[0] = radius
    s.shadow.inherit = False
    return s

def add_text_in_shape(shape, text, size=12, bold=False, color=GRAY_DARK,
                      align=PP_ALIGN.CENTER):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(45720); tf.margin_right = Emu(45720)
    tf.margin_top = Emu(36000); tf.margin_bottom = Emu(36000)
    p = tf.paragraphs[0]; p.alignment = align
    r = p.add_run(); r.text = text
    set_font(r, size=size, bold=bold, color=color)
    return tf

def add_arrow(slide, l, t, w, h, color=GRAY):
    a = slide.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, l, t, w, h)
    a.fill.solid(); a.fill.fore_color.rgb = color
    a.line.fill.background(); a.shadow.inherit = False
    return a

def add_line(slide, x1, y1, x2, y2, color=GRAY, weight=1.5):
    line = slide.shapes.add_connector(1, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line

# ========== 创建演示文稿（单页） ==========
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])

# 背景
add_rect(s, Inches(0), Inches(0), Inches(13.333), Inches(7.5), BG, radius=0)

# =================== 顶部标题栏 ===================
add_rect(s, Inches(0), Inches(0), Inches(13.333), Inches(0.75), NAVY, radius=0)
add_text(s, Inches(0.4), Inches(0.1), Inches(8), Inches(0.4),
         "1+N 数字员工框架 · Skill 自演进进展", size=20, bold=True, color=WHITE)
add_text(s, Inches(0.4), Inches(0.45), Inches(8), Inches(0.3),
         "v3 PR 闭环模式  |  rev-01 v2 真实 UI 测试  |  5 项 P0/P1 关键修复",
         size=11, color=LIGHT_BLUE)
add_text(s, Inches(10.5), Inches(0.2), Inches(2.7), Inches(0.4),
         "汇报日期：2026-07-08", size=10, color=LIGHT_BLUE, align=PP_ALIGN.RIGHT)

# =================== 左侧：4 阶闭环图 ===================
# 图区背景
add_rect(s, Inches(0.3), Inches(1.0), Inches(7.2), Inches(5.0), WHITE, line=GRAY_LIGHT, radius=0.04)
add_text(s, Inches(0.5), Inches(1.1), Inches(7), Inches(0.3),
         "🔄  核心：Skill 自演化四阶闭环 v3", size=13, bold=True, color=NAVY)

# 4 个阶段卡片：左上 → 右上 → 右下 → 左下（顺时针）
# 坐标计算：图区 0.3~7.5, 1.0~6.0
# 阶段卡片尺寸：2.8 × 1.5
# 顺时针布局
stage_w = Inches(2.7); stage_h = Inches(1.5)
gap_x = Inches(0.45); gap_y = Inches(0.5)
# 整体居中起点
group_w = stage_w * 2 + gap_x
group_h = stage_h * 2 + gap_y
gx0 = Inches(0.55)  # (7.2 - group_w) / 2 + 0.3 ≈ 0.55
gy0 = Inches(1.65)  # 图区中心起点

# 左上：分析
tl_x, tl_y = gx0, gy0
tl = add_rect(s, tl_x, tl_y, stage_w, stage_h, ORANGE, line=ORANGE, radius=0.1)
tf = tl.text_frame; tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "① analysis 诊断"
set_font(r1, size=15, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "by analysis"
set_font(r2, size=9, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "读 session + spec + rev-01 意见"
set_font(r3, size=10, color=WHITE)
p4 = tf.add_paragraph(); p4.alignment = PP_ALIGN.CENTER
r4 = p4.add_run(); r4.text = "→ diagnosis.json + skillopt:pending"
set_font(r4, size=10, bold=True, color=WHITE)

# 右上：修改
tr_x = gx0 + stage_w + gap_x
tr_y = gy0
tr = add_rect(s, tr_x, tr_y, stage_w, stage_h, BLUE, line=BLUE, radius=0.1)
tf = tr.text_frame; tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "② skillopt-01 改 skill"
set_font(r1, size=15, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "by skillopt-01"
set_font(r2, size=9, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "改 aid-workflow-skills + 开分支"
set_font(r3, size=10, color=WHITE)
p4 = tf.add_paragraph(); p4.alignment = PP_ALIGN.CENTER
r4 = p4.add_run(); r4.text = "→ commit + [regression] issue"
set_font(r4, size=10, bold=True, color=WHITE)

# 右下：回归
br_x = tr_x
br_y = gy0 + stage_h + gap_y
br = add_rect(s, br_x, br_y, stage_w, stage_h, GREEN, line=GREEN, radius=0.1)
tf = br.text_frame; tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "③ dev-02 沙箱回归"
set_font(r1, size=15, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "by dev-02"
set_font(r2, size=9, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "拉新 skill + 跑完整 AID-Workflow"
set_font(r3, size=10, color=WHITE)
p4 = tf.add_paragraph(); p4.alignment = PP_ALIGN.CENTER
r4 = p4.add_run(); r4.text = "→ 新制品 + regression-done"
set_font(r4, size=10, bold=True, color=WHITE)

# 左下：裁判
bl_x = gx0
bl_y = br_y
bl = add_rect(s, bl_x, bl_y, stage_w, stage_h, PINK, line=PINK, radius=0.1)
tf = bl.text_frame; tf.clear()
p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
r1 = p1.add_run(); r1.text = "④ analysis 裁判"
set_font(r1, size=15, bold=True, color=WHITE)
p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
r2 = p2.add_run(); r2.text = "by analysis (再次)"
set_font(r2, size=9, color=WHITE)
p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
r3 = p3.add_run(); r3.text = "对比新旧制品 · 不再转回 skillopt"
set_font(r3, size=10, color=WHITE)
p4 = tf.add_paragraph(); p4.alignment = PP_ALIGN.CENTER
r4 = p4.add_run(); r4.text = "→ [approved] / [rejected]"
set_font(r4, size=10, bold=True, color=WHITE)

# 4 个箭头：①→② (顶部横), ②→③ (右侧下), ③→④ (底部横), ④→① (左侧上，红色 REJECTED)
# 顶部横箭头：①→②
arr_y_top = gy0 + Inches(0.55)
add_arrow(s, tl_x + stage_w + Inches(0.02), arr_y_top,
          gap_x - Inches(0.04), Inches(0.18), NAVY)
# 右侧下箭头：②→③
arr_x_right = tr_x + stage_w / 2 - Inches(0.09)
add_line(s,
         arr_x_right + 4572000, tr_y + stage_h + Inches(0.02),
         arr_x_right + 4572000, br_y - Inches(0.02),
         color=NAVY, weight=2)
# 底部横箭头：③→④（反向，从右到左）
add_arrow(s, bl_x + Inches(0.02), bl_y + Inches(0.55),
          gap_x - Inches(0.04), Inches(0.18), NAVY)
# 左侧上箭头：④→①（红色 REJECTED）
arr_x_left = bl_x + stage_w / 2 - Inches(0.09)
add_line(s,
         arr_x_left + 4572000, bl_y - Inches(0.02),
         arr_x_left + 4572000, tl_y + stage_h + Inches(0.02),
         color=RED, weight=2)
# REJECTED 标签
add_text(s, gx0 - Inches(0.45), tl_y + stage_h + Inches(0.1),
         Inches(0.6), Inches(0.25),
         "REJECTED", size=8, bold=True, color=RED, align=PP_ALIGN.CENTER)

# 图下方注解
add_text(s, Inches(0.5), Inches(5.55), Inches(7), Inches(0.3),
         "🟢 成功路径：分析 → 修改 → 回归 → 裁判 → 合入 main",
         size=11, bold=True, color=GREEN, align=PP_ALIGN.CENTER)
add_text(s, Inches(0.5), Inches(5.78), Inches(7), Inches(0.25),
         "🔴 REJECTED 路径：裁判不通过时打回 ② skillopt-01 重做（不触发 analysis，避免死循环）",
         size=10, color=RED, align=PP_ALIGN.CENTER)

# =================== 右侧：4 项核心进展 ===================
add_rect(s, Inches(7.7), Inches(1.0), Inches(5.4), Inches(5.0), WHITE, line=GRAY_LIGHT, radius=0.04)
add_text(s, Inches(7.85), Inches(1.1), Inches(5), Inches(0.3),
         "🎯  4 项核心进展", size=13, bold=True, color=NAVY)

progress = [
    ("①", "四阶闭环 v3", "Skill 修改从单向链升级为「分析→修改→回归→裁判」闭环", "杜绝 skillopt→dev-02→analysis→skillopt 死循环", BLUE),
    ("②", "dev-02 沙箱回归", "复用 1+N 既有 agent 体系，开辟独立回归沙箱", "12 个历史 issue 作为基准测试语料，量化 Skill 改动有效性", GREEN),
    ("③", "rev-01 v2 升级", "SOUL.md 15→162 行，亲手跑 UI + 自构 ≥8 补充用例 + ≥8 截图", "dev-01 提交的代码必须在 DevEco 模拟器上真的能跑通", ORANGE),
    ("④", "5 项 P0/P1 修复", "SOUL.md 注入 / skillopt 超时 / dev-02 漏配 / judge 3 bug / NameError", "2026-07-07 同日完成，让闭环从设计变成可执行", RED),
]
py = 1.5
for num, title, line1, line2, color in progress:
    # 左侧色块
    add_rect(s, Inches(7.85), Inches(py), Inches(0.5), Inches(1.0), color, radius=0.15)
    add_text_in_shape(add_rect(s, Inches(7.85), Inches(py), Inches(0.5), Inches(1.0), color, radius=0.15),
                      num, size=20, bold=True, color=WHITE)
    # 标题
    add_text(s, Inches(8.5), Inches(py), Inches(4.4), Inches(0.3),
             title, size=12, bold=True, color=color)
    # 内容
    add_text(s, Inches(8.5), Inches(py + 0.3), Inches(4.4), Inches(0.35),
             line1, size=9.5, color=GRAY_DARK)
    add_text(s, Inches(8.5), Inches(py + 0.65), Inches(4.4), Inches(0.35),
             line2, size=9.5, bold=True, color=color)
    py += 1.1

# =================== 底部：关键决策 + 下一步 ===================
# 关键决策
add_rect(s, Inches(0.3), Inches(6.15), Inches(7.2), Inches(1.25), GRAY_LIGHT, radius=0.05)
add_text(s, Inches(0.5), Inches(6.25), Inches(7), Inches(0.3),
         "💡  关键设计决策", size=12, bold=True, color=NAVY)
add_text(s, Inches(0.5), Inches(6.55), Inches(7), Inches(0.85),
         "❶ 不采用 SkillOpt 框架：1+N 体系本身就是「人驱动的 SkillOpt」，可解释、可审计、零迁移成本\n"
         "❷ dev-02 复用 1+N 基础设施：独立 Hermes profile + 独立 PAT，Skill 源严格隔离（拉测试 skill，非生产 skill）\n"
         "❸ analysis 闭环不回转：避免死循环，由人决定是否再开 PR",
         size=9, color=GRAY_DARK)

# 下一步
add_rect(s, Inches(7.7), Inches(6.15), Inches(5.4), Inches(1.25), GRAY_LIGHT, radius=0.05)
add_text(s, Inches(7.85), Inches(6.25), Inches(5), Inches(0.3),
         "🚀  下一步计划", size=12, bold=True, color=NAVY)
add_text(s, Inches(7.85), Inches(6.55), Inches(5.2), Inches(0.85),
         "•  短期（1-2 周）：跑通 issue #34 完整 v3 闭环，验证 analysis 闭环只 judge\n"
         "•  中期（1 月）：采集 12 issue 回归基线（compile_rate / test_rate / ui_rate）\n"
         "•  长期（季度）：推进 SOUL 单一真理源 + Skill 改动审计日志全留痕",
         size=9, color=GRAY_DARK)

# 页脚
add_text(s, Inches(0.4), Inches(7.2), Inches(13), Inches(0.3),
         "1+N 框架团队  ·  D:/huawei/Demo/  ·  1 / 1",
         size=9, color=GRAY, align=PP_ALIGN.CENTER)

# 保存
out = "D:/huawei/Demo/_upload_target/1plusn-skill-evolution-onepage-2026-07-08.pptx"
prs.save(out)
import sys; sys.stdout.reconfigure(encoding='utf-8')
print(f"[OK] saved: {out}")
print(f"     slides: {len(prs.slides)}")

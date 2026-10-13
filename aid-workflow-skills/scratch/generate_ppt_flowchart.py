"""
Skill 自优化流程图 — 单页 PPT
"""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.oxml.ns import qn
from lxml import etree

NAVY = RGBColor(0x0B, 0x2E, 0x59)
ORANGE = RGBColor(0xE6, 0x5C, 0x00)
BLUE = RGBColor(0x1E, 0x88, 0xE5)
GREEN = RGBColor(0x2E, 0x7D, 0x32)
PINK = RGBColor(0xAD, 0x14, 0x57)
RED = RGBColor(0xC0, 0x39, 0x2B)
GRAY = RGBColor(0x75, 0x75, 0x75)
GRAY_LIGHT = RGBColor(0xF5, 0xF5, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY_DARK = RGBColor(0x33, 0x33, 0x33)
LIGHT_BLUE = RGBColor(0xE3, 0xF2, 0xFD)
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

def add_line(slide, x1, y1, x2, y2, color=GRAY, weight=2):
    line = slide.shapes.add_connector(1, Emu(x1), Emu(y1), Emu(x2), Emu(y2))
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line

# ====== 创建演示文稿（单页）======
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)
s = prs.slides.add_slide(prs.slide_layouts[6])

# 标题
add_text(s, Inches(0.5), Inches(0.3), Inches(12), Inches(0.5),
         "Skill 自优化流程图（v3 PR 闭环模式）",
         size=22, bold=True, color=NAVY)
add_text(s, Inches(0.5), Inches(0.85), Inches(12), Inches(0.3),
         "1+N 数字员工框架  ·  analysis → skillopt-01 → dev-02 → analysis 裁判",
         size=12, color=GRAY)

# ====== 4 阶闭环：横向单行排列 ======
# 阶段卡片尺寸
sw = Inches(2.55); sh = Inches(2.4); gap = Inches(0.45)
# 整体居中
total_w = sw * 4 + gap * 3
sx0 = (Inches(13.333) - total_w) / 2
sy = Inches(2.0)

stages = [
    ("① 诊断", "analysis", "读 session + spec\n+ rev-01 意见", "diagnosis.json\n+ skillopt:pending", ORANGE),
    ("② 改 skill", "skillopt-01", "改 aid-workflow-skills\n开分支", "commit + [regression]\nissue", BLUE),
    ("③ 沙箱回归", "dev-02", "拉新 skill\n跑完整 AID-Workflow", "新制品 + 测试报告\n+ regression-done", GREEN),
    ("④ 裁判", "analysis", "对比新旧制品\n判定有效性", "[approved] / [rejected]\n不再转回 skillopt", PINK),
]
for i, (title, agent, action, output, color) in enumerate(stages):
    x = sx0 + (sw + gap) * i
    # 阶段标题色条
    title_bar = add_rect(s, x, sy, sw, Inches(0.5), color, radius=0.1)
    tf = title_bar.text_frame
    tf.clear()
    p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run(); r1.text = title
    set_font(r1, size=16, bold=True, color=WHITE)
    # 主体
    body = add_rect(s, x, sy + Inches(0.5), sw, sh - Inches(0.5), WHITE, line=color, radius=0.06)
    tf = body.text_frame
    tf.clear()
    tf.margin_left = Emu(72000); tf.margin_right = Emu(72000)
    tf.margin_top = Emu(80000); tf.margin_bottom = Emu(80000)
    p1 = tf.paragraphs[0]; p1.alignment = PP_ALIGN.CENTER
    r1 = p1.add_run(); r1.text = f"by {agent}"
    set_font(r1, size=10, bold=True, color=color)
    p2 = tf.add_paragraph(); p2.alignment = PP_ALIGN.CENTER
    r2 = p2.add_run(); r2.text = " "
    set_font(r2, size=4)
    p3 = tf.add_paragraph(); p3.alignment = PP_ALIGN.CENTER
    r3 = p3.add_run(); r3.text = "📥 输入"
    set_font(r3, size=9, bold=True, color=GRAY)
    p4 = tf.add_paragraph(); p4.alignment = PP_ALIGN.CENTER
    r4 = p4.add_run(); r4.text = action
    set_font(r4, size=10, color=GRAY_DARK)
    p5 = tf.add_paragraph(); p5.alignment = PP_ALIGN.CENTER
    r5 = p5.add_run(); r5.text = " "
    set_font(r5, size=4)
    p6 = tf.add_paragraph(); p6.alignment = PP_ALIGN.CENTER
    r6 = p6.add_run(); r6.text = "📤 输出"
    set_font(r6, size=9, bold=True, color=color)
    p7 = tf.add_paragraph(); p7.alignment = PP_ALIGN.CENTER
    r7 = p7.add_run(); r7.text = output
    set_font(r7, size=10, bold=True, color=color)
    # 箭头
    if i < 3:
        add_arrow(s, x + sw + Inches(0.05), sy + Inches(1.05),
                  gap - Inches(0.1), Inches(0.3), NAVY)

# ====== 下方 REJECTED 反馈弧线（从 ④ 回到 ②）======
# 在 ② ③ 之间下方的弧线
rej_y = sy + sh + Inches(0.4)
add_text(s, Inches(0.5), rej_y, Inches(12.3), Inches(0.3),
         "↩  REJECTED 反馈：④ 裁判不通过时，打回 ② skillopt-01 重新修改（不触发 analysis，避免死循环）",
         size=12, bold=True, color=RED, align=PP_ALIGN.CENTER)

# 用弯箭头：从 ④ 下方回到 ② 下方
# ④ 卡片底部中点
rej_arrow_y = rej_y + Inches(0.35)
# 左侧起点：④ 卡片下方  (sx0 + (sw+gap)*3 + sw/2)
start_x = sx0 + (sw + gap) * 3 + sw / 2
# 终点：② 卡片下方 (sx0 + (sw+gap)*1 + sw/2)
end_x = sx0 + (sw + gap) * 1 + sw / 2
# 画一条曲线
from pptx.enum.shapes import MSO_CONNECTOR
connector = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, start_x, rej_arrow_y,
                                    start_x, rej_arrow_y + Inches(0.4))
connector.line.color.rgb = RED; connector.line.width = Pt(2)
# 横线
h_line = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, end_x, rej_arrow_y + Inches(0.4),
                                 start_x, rej_arrow_y + Inches(0.4))
h_line.line.color.rgb = RED; h_line.line.width = Pt(2)
# 向上箭头到 ②
v_line = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, end_x, rej_arrow_y + Inches(0.4),
                                 end_x, sy + sh + Inches(0.05))
v_line.line.color.rgb = RED; v_line.line.width = Pt(2)
# 加一个向上的小箭头
arr = s.shapes.add_shape(MSO_SHAPE.UP_ARROW, end_x - Inches(0.1),
                          sy + sh - Inches(0.05), Inches(0.2), Inches(0.25))
arr.fill.solid(); arr.fill.fore_color.rgb = RED
arr.line.fill.background(); arr.shadow.inherit = False

# ====== 底部注解 ======
foot_y = Inches(6.8)
add_text(s, Inches(0.5), foot_y, Inches(12.3), Inches(0.4),
         "✅  成功路径：合入 main，Skill 升级生效       🔴  REJECTED 路径：打回 skillopt-01 重做（最多 N 轮）",
         size=11, color=GRAY_DARK, align=PP_ALIGN.CENTER)

# 保存
out = "D:/huawei/Demo/_upload_target/skill-optimization-flowchart.pptx"
prs.save(out)
import sys; sys.stdout.reconfigure(encoding='utf-8')
print(f"[OK] saved: {out}")
print(f"     slides: {len(prs.slides)}")

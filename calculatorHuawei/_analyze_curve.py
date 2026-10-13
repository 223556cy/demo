#!/usr/bin/env python3
# 分析截图中的蓝色曲线像素位置
import sys
from PIL import Image
import numpy as np

img = Image.open('D:/huawei/Demo/calculatorHuawei/_ui_test/07_test_xx.png').convert('RGB')
arr = np.array(img)
H, W, _ = arr.shape
print(f'image: {W}x{H}')

# 找到蓝色曲线 (curveColor=#4684E3)
# RGB: (70, 132, 227)
target = np.array([70, 132, 227])
# 阈值匹配
diff = np.abs(arr.astype(int) - target).sum(axis=2)
mask = diff < 80  # 蓝色像素

# 排除顶部 (状态栏) 和底部 (键盘)，只看 canvas 区域
# 假设 canvas 大约在 y=[200, 1700] 范围
mask[:200, :] = False
mask[1700:, :] = False

# 每一列（x）找到蓝色像素的 y 位置
ys_per_x = []
for x in range(W):
    col = mask[:, x]
    ys = np.where(col)[0]
    if len(ys) > 0:
        # 取中间值（中位数）避免噪声
        ys_per_x.append((x, int(np.median(ys))))

print(f'找到 {len(ys_per_x)} 列含蓝色像素')

# 取一些样本点
import re
# 根据 xMin/xMax 标签 (-7 到 7) 和 label 位置估计 data x 范围
# 标签 -7 应该在最左边 (canvas x≈80), 7 在最右边 (canvas x≈1240)
# 约线性: canvas_x = 80 + (x_data + 7) / 14 * (1240-80) = 80 + (x+7)/14*1160

# 反推: y_canvas 高低. 范围 ~[200, 1700]
# X axis (y=0 data) 在 canvas 的什么位置？

# 收集所有点的 y_min 和 y_max 来估计
if ys_per_x:
    all_ys = [y for _, y in ys_per_x]
    print(f'curve y 范围: {min(all_ys)} 到 {max(all_ys)}, 中位数={int(np.median(all_ys))}')

# 输出曲线轨迹（每隔一定 x 间隔）
print('\n曲线轨迹 (x_canvas, y_canvas):')
for i in range(0, len(ys_per_x), max(1, len(ys_per_x)//30)):
    x_c, y_c = ys_per_x[i]
    # 估算数据 x: x_c ≈ 80 + (x_data + 7)/14 * 1160
    x_data = (x_c - 80) / 1160 * 14 - 7
    print(f'  canvas=({x_c:4d},{y_c:4d})  ~data x={x_data:+5.2f}')

# 对比 sin(x) 在相同 canvas 位置
print('\n参考 sin(x) 在 data x=-6.28..6.28 上理论 canvas y:')
PAD_T, PAD_B = 20, 30
inner_top, inner_bot = 200, 1700
inner_h = inner_bot - inner_top
yMin_data, yMax_data = -1.2, 1.2  # 假设标准
for x_data in [-6.28, -3.14, -1.57, 0, 1.57, 3.14, 6.28]:
    y_data = np.sin(x_data)
    y_canvas = inner_top + (1 - (y_data - yMin_data)/(yMax_data - yMin_data)) * inner_h
    print(f'  data=({x_data:+5.2f},{y_data:+6.3f})  expected canvas y={y_canvas:.0f}')
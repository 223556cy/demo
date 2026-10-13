#!/usr/bin/env python3
"""精确分析 canvas 中的坐标轴和曲线"""
import sys
import numpy as np
from PIL import Image

img = Image.open('D:/huawei/Demo/calculatorHuawei/_ui_test/07_test_xx.png').convert('RGB')
arr = np.array(img)
H, W, _ = arr.shape

# 1. 找黑色像素 (axes)
black = (arr.sum(axis=2) < 80)  # 黑色
# 限制到 canvas 区域 (y < 1700 避免键盘)
black[1700:, :] = False

# 2. 找垂直线 (Y axis)
vlines = []
for x in range(W):
    col_black = black[:, x].sum()
    if col_black > 100:  # 一列里有 > 100 个黑色像素
        vlines.append((x, col_black))
print(f'垂直黑线候选 (col, count):')
for x, c in vlines[:10]:
    print(f'  canvas x={x}: {c} pixels')

# 3. 找水平线 (X axis)
hlines = []
for y in range(H):
    row_black = black[y, :].sum()
    if row_black > 200:  # 一行里有 > 200 个黑色像素
        hlines.append((y, row_black))
print(f'\n水平黑线候选 (row, count):')
for y, c in hlines[:20]:
    print(f'  canvas y={y}: {c} pixels')

# 4. 蓝色曲线
blue_target = np.array([70, 132, 227])
blue_diff = np.abs(arr.astype(int) - blue_target).sum(axis=2)
blue_mask = blue_diff < 80
blue_mask[1700:, :] = False  # 排除键盘

# 蓝色像素的 y 分布
ys_blue, xs_blue = np.where(blue_mask)
print(f'\n蓝色曲线像素范围:')
print(f'  x: {xs_blue.min()} 到 {xs_blue.max()}')
print(f'  y: {ys_blue.min()} 到 {ys_blue.max()}')
print(f'  总像素: {len(xs_blue)}')

# 找 y 轴位置 (vertical line)
v_axis_x = max(vlines, key=lambda x: x[1])[0] if vlines else None
print(f'\nY axis 推测位置: canvas x={v_axis_x}')

# 找 x 轴位置 (horizontal line)
h_axis_y = max(hlines, key=lambda x: x[1])[0] if hlines else None
print(f'X axis 推测位置: canvas y={h_axis_y}')

# 根据 v_axis_x 估算 data x 范围
# v_axis_x = data x=0
# 假设 X 轴标签 -7 和 7 在 canvas 边缘附近
# 蓝色像素 x 范围: {xs_blue.min()} 到 {xs_blue.max()}

# 用蓝色像素反推数据 x 范围
# 假设 data x 范围从蓝色最左到最右（或者标签边界）
if v_axis_x and xs_blue.size > 0:
    # X=0 在 v_axis_x, X=2π=6.28 在某处
    # 如果蓝色最右是 data x=+6.28
    x_min_canvas = xs_blue.min()
    x_max_canvas = xs_blue.max()
    # data x in [-6.28, +6.28] 对应 canvas x in [x_min, x_max]
    # v_axis_x = data x=0
    print(f'\n基于 Y axis 位置 v_axis_x={v_axis_x} 推算 data x 范围:')
    print(f'  蓝色像素 x 范围: {x_min_canvas} 到 {x_max_canvas}')
    # 假设 data x 范围等于蓝色范围 (覆盖整个 plot)
    # v_axis_x 应该是 data x=0 的位置
    # 但蓝色覆盖可能不完整（直线只覆盖部分 y_data）
    # 用采样点 i=0, i=199 推算: 假设 i=0 是 data x=xMin, i=199 是 data x=xMax
    # 但不知道 xMin/xMax 实际值

    # 推测: xMin=-6.28, xMax=6.28
    # canvas x = paddingLeft + (data x - xMin)/(xMax-xMin) * innerW
    # innerW = W - PAD_L - PAD_R = 1320 - 40 - 20 = 1260
    # 假设 PAD_L=40, PAD_R=20
    PAD_L, PAD_R = 40, 20
    inner_w = W - PAD_L - PAD_R
    xMin_d, xMax_d = -6.28, 6.28
    # Y axis 应该 canvas x = PAD_L + (0-xMin)/(xMax-xMin) * innerW = 40 + 630 = 670
    print(f'  理论 Y axis canvas x (xMin=-6.28,xMax=+6.28): {PAD_L + (0-xMin_d)/(xMax_d-xMin_d)*inner_w:.0f}')
    print(f'  实际找到: {v_axis_x}')

# 5. 在每个 X 列找蓝色 y，画出曲线轨迹
print('\n蓝色曲线轨迹 (canvas y vs canvas x):')
for x in range(xs_blue.min(), xs_blue.max()+1, max(1, (xs_blue.max()-xs_blue.min())//30)):
    col = blue_mask[:, x]
    ys = np.where(col)[0]
    if len(ys) > 0:
        print(f'  canvas x={x:4d}: y median={int(np.median(ys)):4d}')
"""
Plot speed traces with corner annotations and interactive features
==================================================================

Plot the speed over the course of a lap, add annotations to mark corners,
and dynamically display the speed of both drivers along with the speed difference
based on the mouse's X-axis position. A vertical line will indicate the distance.
"""

import matplotlib.pyplot as plt
import fastf1.plotting
import fastf1
import numpy as np
from itertools import cycle

# 参数设置：修改这里来选择年份、比赛名称、session identifier 和车手列表
YEAR = 2024
GRAND_PRIX = 'Chinese Grand Prix'
SESSION_IDENTIFIER = 'Q'  # 可以是 'FP1', 'FP2', 'FP3', 'Q', 'R' 等
DRIVERS = ['BOT', 'ZHO']  # 填入你想对比的车手代码列表，例如 ['VER', 'HAM']

# Enable Matplotlib patches for plotting timedelta values and load
# FastF1's dark color scheme
fastf1.plotting.setup_mpl(mpl_timedelta_support=True, misc_mpl_mods=False, color_scheme='fastf1')

# Load a session and its telemetry data
session = fastf1.get_session(YEAR, GRAND_PRIX, SESSION_IDENTIFIER)
session.load()

# 设置颜色循环
color_cycle = cycle(fastf1.plotting.COLOR_PALETTE)

# 创建绘图
fig, ax = plt.subplots()

# 用于保存各车手的速度数据和插值后的速度差
car_data_list = []

# 遍历选择的车手，获取各自最快圈速并绘制速度轨迹
for driver in DRIVERS:
    # 获取车手的最快圈速
    fastest_lap = session.laps.pick_driver(driver).pick_fastest()
    car_data = fastest_lap.get_car_data().add_distance()
    car_data_list.append(car_data)
    team_color = next(color_cycle)

    # 绘制车手的速度轨迹
    ax.plot(car_data['Distance'], car_data['Speed'], color=team_color, label=fastest_lap['Driver'])

# 插值计算速度差
if len(car_data_list) == 2:
    car_data_1, car_data_2 = car_data_list
    common_distance = np.linspace(
        max(car_data_1['Distance'].min(), car_data_2['Distance'].min()),
        min(car_data_1['Distance'].max(), car_data_2['Distance'].max()),
        num=1000
    )

    speed_1_interp = np.interp(common_distance, car_data_1['Distance'], car_data_1['Speed'])
    speed_2_interp = np.interp(common_distance, car_data_2['Distance'], car_data_2['Speed'])
    speed_diff = speed_1_interp - speed_2_interp

# 绘制弯角标记
v_min = min(min(car_data['Speed']) for car_data in car_data_list)
v_max = max(max(car_data['Speed']) for car_data in car_data_list)
circuit_info = session.get_circuit_info()
ax.vlines(x=circuit_info.corners['Distance'], ymin=v_min-20, ymax=v_max+20, linestyles='dotted', colors='grey')

# 在每个垂直线下方标注弯角编号
for _, corner in circuit_info.corners.iterrows():
    txt = f"{corner['Number']}{corner['Letter']}"
    ax.text(corner['Distance'], v_min-30, txt, va='center_baseline', ha='center', size='small')

# 获取赛道总长
track_length = max(car_data_1['Distance'].max(), car_data_2['Distance'].max())

ax.set_xlim(0, track_length)  # 限制x轴为0到赛道总长
ax.set_xlabel('Distance in m')
ax.set_ylabel('Speed in km/h')
ax.legend()

# 添加动态显示框用于显示速度差
text_box = ax.text(0.02, 0.95, '', transform=ax.transAxes, fontsize=12, verticalalignment='top')

# 添加垂直线指示器
vline = ax.axvline(x=0, color='red', linestyle='--')

# 定义鼠标移动事件响应函数
def on_mouse_move(event):
    if event.inaxes != ax:
        return

    # 获取鼠标的x位置（距离）
    distance = event.xdata

    # 限制 distance 在 0 和 track_length 之间
    if distance is None:
        return
    distance = max(0, min(distance, track_length))

    # 更新垂直线的位置，将 distance 转换为序列
    vline.set_xdata([distance])

    # 获取车手在当前距离的速度
    speed_1 = np.interp(distance, car_data_1['Distance'], car_data_1['Speed'])
    speed_2 = np.interp(distance, car_data_2['Distance'], car_data_2['Speed'])
    speed_difference = speed_1 - speed_2

    # 更新显示的文本
    text_box.set_text(
        f"Distance: {distance:.1f} m\n"
        f"{DRIVERS[0]} Speed: {speed_1:.1f} km/h\n"
        f"{DRIVERS[1]} Speed: {speed_2:.1f} km/h\n"
        f"Speed Difference: {speed_difference:.1f} km/h"
    )
    fig.canvas.draw_idle()

# 连接鼠标移动事件
fig.canvas.mpl_connect('motion_notify_event', on_mouse_move)

plt.show()

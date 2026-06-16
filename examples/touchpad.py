"""
触摸板示例
==========
将 DualSense 触摸板模拟为电脑触摸板。

单指：
  移动        → 鼠标移动
  轻触（短按）→ 左键单击
  双击        → 左键双击

双指：
  上下移动    → 滚轮滚动
  轻触（短按）→ 右键单击

触摸板实体键：
  单指/无指   → 左键单击
  双指        → 右键单击

PS 键 → 退出
"""

import os
import sys
import time
import pyautogui

os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dualforge import DualForge

# ── 参数调节 ──────────────────────────────────────────────────
MOVE_SPEED      = 1.0    # 鼠标移动速度倍率
SCROLL_SPEED    = 0.8   # 滚轮速度倍率
TAP_MAX_TIME    = 0.3    # 轻触最长时间（秒），超过则视为拖动
TAP_MAX_MOVE    = 40     # 轻触最大移动距离（触摸板像素），超过则视为拖动
DOUBLE_TAP_TIME = 0.3    # 双击间隔最长时间（秒）

pyautogui.FAILSAFE = False
pyautogui.PAUSE    = 0

# ── 全局状态 ──────────────────────────────────────────────────
finger0_prev      = {'touching': False, 'x': 0, 'y': 0}
finger0_down_time = 0.0
finger0_down_pos  = (0, 0)
finger0_dragging  = False

finger1_prev      = {'touching': False, 'x': 0, 'y': 0}
two_finger_prev_y = 0
two_finger_start_time = 0.0
two_finger_down_time = 0.0


last_tap_time = 0.0

prev_home = False
prev_pad  = False

ds = DualForge()


def update(s):
    global finger0_prev, finger0_down_time, finger0_down_pos, finger0_dragging
    global finger1_prev, two_finger_prev_y, two_finger_start_time, two_finger_down_time
    global last_tap_time
    global prev_home, prev_pad

    home = s['buttons']['home']
    pad  = s['buttons']['pad']
    f0   = s['touch']['finger'][0]
    f1   = s['touch']['finger'][1]

    now = time.time()

    # ── PS 键退出 ─────────────────────────────────────────────
    if home and not prev_home:
        print("\n退出程序")
        ds.set_led(0, 0, 0)
        ds.disconnect()
        os._exit(0)

    # ── 触摸板实体键 ──────────────────────────────────────────────
    if pad and not prev_pad:
        if f0['touching'] and f1['touching']:
            pyautogui.click(button='right')
            print("右键单击（实体键）")
        else:
            pyautogui.mouseDown()  # 按住左键，不释放
            print("左键按下（拖动模式）")

    if not pad and prev_pad:
        pyautogui.mouseUp()  # 松开左键
        print("左键释放")

    # ── 双指模式 ──────────────────────────────────────────────────

    if f0['touching'] and f1['touching']:

        # 双指刚落下，冻结鼠标，记录时间和初始Y
        if not (finger0_prev['touching'] and finger1_prev['touching']):
            two_finger_start_time = now
            two_finger_down_time = now
            two_finger_prev_y = (f0['y'] + f1['y']) / 2
            # 如果单指正在移动，立刻停止
            finger0_dragging = False

        # 稳定期后才滚动，期间鼠标完全不动
        elif now - two_finger_start_time > 0.15:
            avg_y_now = (f0['y'] + f1['y']) / 2
            avg_y_prev = (finger0_prev['y'] + finger1_prev['y']) / 2
            dy = avg_y_now - avg_y_prev
            if abs(dy) > 1:
                pyautogui.scroll(int(dy * SCROLL_SPEED))

    # 双指 → 有手指抬起
    elif finger0_prev['touching'] and finger1_prev['touching']:
        if not f0['touching'] or not f1['touching']:  # ← 从 and 改成 or
            duration = now - two_finger_down_time
            if duration < TAP_MAX_TIME:
                pyautogui.click(button='right')
                print("右键单击")

    # ── 单指模式 ──────────────────────────────────────────────
    elif f0['touching'] and not f1['touching']:

        # 单指刚落下
        if not finger0_prev['touching']:
            finger0_down_time = now
            finger0_down_pos  = (f0['x'], f0['y'])
            finger0_dragging  = False

        # 单指移动中
        elif finger0_prev['touching']:
            dx = f0['x'] - finger0_prev['x']
            dy = f0['y'] - finger0_prev['y']

            total_move = abs(f0['x'] - finger0_down_pos[0]) + \
                         abs(f0['y'] - finger0_down_pos[1])

            hold_time = now - finger0_down_time

            # 移动超过阈值 或 按住超过 0.15 秒 → 判定为拖动
            if total_move > TAP_MAX_MOVE or hold_time > 0.15:
                finger0_dragging = True

            # 只有确认是拖动才移动鼠标
            if finger0_dragging and (abs(dx) > 0 or abs(dy) > 0):
                pyautogui.moveRel(dx * MOVE_SPEED, dy * MOVE_SPEED)
            elif pad and (abs(dx) > 0 or abs(dy) > 0):  # ← 加这行
                pyautogui.moveRel(dx * MOVE_SPEED, dy * MOVE_SPEED)

    # 单指刚抬起
    elif finger0_prev['touching'] and not f1['touching'] and not f0['touching']:
        duration = now - finger0_down_time

        if not finger0_dragging and duration < TAP_MAX_TIME:
            if now - last_tap_time < DOUBLE_TAP_TIME:
                pyautogui.doubleClick()
                print("左键双击")
                last_tap_time = 0.0
            else:
                pyautogui.click()
                print("左键单击")
                last_tap_time = now

    finger0_prev = dict(f0)
    finger1_prev = dict(f1)
    prev_home    = home
    prev_pad     = pad


@ds.on_state
def on_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")
    if not connected:
        os._exit(0)


@ds.on_input
def on_input(s):
    update(s)


print("=" * 50)
print("DualSense 触摸板模拟")
print("  单指移动      → 鼠标移动")
print("  单指轻触      → 左键单击")
print("  单指双击      → 左键双击")
print("  双指移动      → 滚轮滚动")
print("  双指轻触      → 右键单击")
print("  实体键（单指）→ 左键单击")
print("  实体键（双指）→ 右键单击")
print("  PS 键         → 退出")
print("=" * 50)

ds.connect()
ds.set_led(0, 200, 255)

while True:
    time.sleep(1)
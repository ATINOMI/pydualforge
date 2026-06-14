"""
弓弦模拟示例 v4
==============
连接后一次性设置 Bow 效果，固件自动处理弹性手感。
只监听扳机深度控制 LED 和离弦震动。
"""

import os
import sys
import time

os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dualforge import DualForge, trigger_effects

# ── 参数调节 ──────────────────────────────────────────────
STRENGTH          = 8             # 弓弦阻力（1~8）
SNAP_FORCE        = 6             # 回弹力（1~8）
START_POS         = 0             # 阻力起始区域（0~8）
END_POS           = 8             # 阻力结束区域
BOW_COLOR         = (255, 80, 0)  # 弓弦颜色（橙色）
DRAW_THRESHOLD    = 20            # 判定开始拉弓的阈值
RELEASE_THRESHOLD = 8             # 判定完全松开的阈值
IMPACT_DURATION   = 0.15          # 震动持续时间（秒）
MAX_RUMBLE        = 255           # 最大震动强度（0~255）

# ── 全局状态 ──────────────────────────────────────────────
prev_trigger     = 0
peak_trigger     = 0
release_integral = 0.0
impact_timer     = 0.0
in_impact        = False
is_drawing       = False

ds = DualForge()


def update(s):
    global prev_trigger, peak_trigger, release_integral
    global impact_timer, in_impact, is_drawing

    trigger = s['triggers']['right']

    # ── LED 亮度随深度变化 ────────────────────────────────
    # LED 亮度随深度变化（震动期间不更新）
    if not in_impact:
        ratio = trigger / 255
        r = int(BOW_COLOR[0] * ratio)
        g = int(BOW_COLOR[1] * ratio)
        b = int(BOW_COLOR[2] * ratio)
        ds.set_led(r, g, b)

    # ── 拉弓检测 ──────────────────────────────────────────
    if not is_drawing and trigger > DRAW_THRESHOLD:
        is_drawing = True
        peak_trigger = trigger
        release_integral = 0.0
        print(f"[弓弦] 开始拉弓")

    # ── 拉弓过程 ──────────────────────────────────────────
    if is_drawing:
        if trigger > peak_trigger:
            peak_trigger = trigger

        if trigger < prev_trigger:
            release_integral += (prev_trigger - trigger)

        # ── 离弦检测 ──────────────────────────────────────
        if trigger <= RELEASE_THRESHOLD and not in_impact:
            is_drawing = False

            rumble = int(release_integral / 255 * MAX_RUMBLE)
            rumble = max(0, min(255, rumble))
            print(f"[弓弦] 离弦！峰值={peak_trigger} 积分={release_integral:.1f} 震动={rumble}")

            peak_trigger = 0
            release_integral = 0.0

            if rumble > 0:
                ds.set_led(0, 0, 0)  # 先关 LED
                ds.set_rumble(int(rumble/2), rumble)
                impact_timer = time.time()
                in_impact = True

    # ── 震动计时 ──────────────────────────────────────────
    if in_impact and time.time() - impact_timer >= IMPACT_DURATION:
        ds.stop_rumble()
        in_impact = False
        print(f"[弓弦] 待机")

    prev_trigger = trigger


@ds.on_state
def on_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")
    if not connected:
        os._exit(0)


@ds.on_input
def on_input(s):
    update(s)
    if s['buttons']['options']:
        print("退出")
        ds.set_trigger_effect('right', trigger_effects.off())
        ds.set_led(0, 0, 0)
        ds.stop_rumble()
        time.sleep(0.1)
        ds.disconnect()
        os._exit(0)


print("弓弦模拟已启动，按 OPTIONS 键退出")
print(f"参数：阻力={STRENGTH} 回弹={SNAP_FORCE} 颜色={BOW_COLOR}")

ds.connect()

# 连接后一次性设置 Bow，之后不再改变
ds.set_trigger_effect('right', trigger_effects.bow(
    START_POS, END_POS, STRENGTH, SNAP_FORCE
))

try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("退出")
    ds.set_trigger_effect('right', trigger_effects.off())
    ds.set_led(0, 0, 0)
    ds.stop_rumble()
    ds.disconnect()
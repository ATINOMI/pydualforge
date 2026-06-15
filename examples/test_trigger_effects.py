"""
trigger_effects 测试文件
========================
操作说明：
  OPTIONS      → 进入/退出设置模式
  L1 / R1      → 选择左/右扳机（设置模式内）
  方向键 上/下  → 切换效果（设置模式内）
  PS（Home）键 → 退出程序
"""

import os
import sys
import time

os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dualforge import DualForge, trigger_effects, DPad

# ── 效果列表 ──────────────────────────────────────────────────
EFFECTS = [
    ("off",                   lambda: trigger_effects.off()),
    ("normal",                lambda: trigger_effects.normal()),
    ("very_soft",             lambda: trigger_effects.very_soft()),
    ("soft",                  lambda: trigger_effects.soft()),
    ("medium",                lambda: trigger_effects.medium()),
    ("hard",                  lambda: trigger_effects.hard()),
    ("very_hard",             lambda: trigger_effects.very_hard()),
    ("hardest",               lambda: trigger_effects.hardest()),
    ("rigid",                 lambda: trigger_effects.rigid()),
    ("feedback(3, 5)",        lambda: trigger_effects.feedback(3, 5)),
    ("weapon(2, 6, 8)",       lambda: trigger_effects.weapon(2, 6, 8)),
    ("game_cube",             lambda: trigger_effects.game_cube()),
    ("semi_automatic_gun",    lambda: trigger_effects.semi_automatic_gun()),
    ("choppy",                lambda: trigger_effects.choppy()),
    ("bow(0, 8, 7, 6)",       lambda: trigger_effects.bow(0, 8, 7, 6)),
    ("vibration(0, 5, 20)",   lambda: trigger_effects.vibration(0, 5, 20)),
    ("automatic_gun",         lambda: trigger_effects.automatic_gun()),
    ("vibrate_trigger(10)",   lambda: trigger_effects.vibrate_trigger(10)),
    ("vibrate_trigger_pulse", lambda: trigger_effects.vibrate_trigger_pulse()),
    ("machine(1,9,5,3,10,1)", lambda: trigger_effects.machine(1, 9, 5, 3, 10, 1)),
    ("galloping(0,9,2,5,10)", lambda: trigger_effects.galloping(0, 9, 2, 5, 10)),
]

# ── 全局状态 ──────────────────────────────────────────────────
setting_mode   = False
active_trigger = 'right'
left_index     = 0
right_index    = 0

prev_options = False
prev_l1      = False
prev_r1      = False
prev_dpad    = DPad.NONE
prev_home    = False

ds = DualForge()


# ── 清屏 ──────────────────────────────────────────────────────
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


# ── 打印函数 ──────────────────────────────────────────────────
def print_header():
    print("=" * 50)
    print("  扳机效果测试")
    print("  OPTIONS → 进入/退出设置  |  PS键 → 退出")
    print("=" * 50)


def print_status():
    clear()
    print_header()

    if setting_mode:
        print("\n  【设置模式】  L1/R1 选扳机，方向键上下切换\n")
        ds.set_led(0, 100, 255)
    else:
        print("\n  【正常模式】\n")
        ds.set_led(0, 255, 0)

    l_name  = EFFECTS[left_index][0]
    r_name  = EFFECTS[right_index][0]
    arrow_l = ' ◀' if active_trigger == 'left'  else ''
    arrow_r = ' ◀' if active_trigger == 'right' else ''

    print(f"  {'▶' if active_trigger == 'left'  else ' '} 左扳机: [{left_index  + 1:02d}/{len(EFFECTS)}] {l_name}{arrow_l}")
    print(f"  {'▶' if active_trigger == 'right' else ' '} 右扳机: [{right_index + 1:02d}/{len(EFFECTS)}] {r_name}{arrow_r}")


def apply_effect(target: str, index: int):
    name, effect_fn = EFFECTS[index]
    ds.set_trigger_effect(target, effect_fn())
    return name


def update(s):
    global setting_mode, active_trigger
    global left_index, right_index
    global prev_options, prev_l1, prev_r1, prev_dpad, prev_home

    options = s['buttons']['options']
    l1      = s['buttons']['l1']
    r1      = s['buttons']['r1']
    home    = s['buttons']['home']
    dpad    = s['buttons']['dpad']

    # ── PS 键退出 ─────────────────────────────────────────────
    if home and not prev_home:
        clear()
        print("退出程序")
        ds.set_trigger_effect('left',  trigger_effects.off())
        ds.set_trigger_effect('right', trigger_effects.off())
        ds.set_led(0, 0, 0)
        ds.disconnect()
        os._exit(0)

    # ── OPTIONS 进入/退出设置模式 ─────────────────────────────
    if options and not prev_options:
        setting_mode = not setting_mode
        print_status()

    if setting_mode:

        # ── L1 选择左扳机 ─────────────────────────────────────
        if l1 and not prev_l1:
            active_trigger = 'left'
            print_status()

        # ── R1 选择右扳机 ─────────────────────────────────────
        if r1 and not prev_r1:
            active_trigger = 'right'
            print_status()

        # ── 方向键下：下一个效果 ──────────────────────────────
        if dpad == DPad.SOUTH and prev_dpad != DPad.SOUTH:
            if active_trigger == 'right':
                right_index = (right_index + 1) % len(EFFECTS)
                apply_effect('right', right_index)
            else:
                left_index = (left_index + 1) % len(EFFECTS)
                apply_effect('left', left_index)
            print_status()

        # ── 方向键上：上一个效果 ──────────────────────────────
        if dpad == DPad.NORTH and prev_dpad != DPad.NORTH:
            if active_trigger == 'right':
                right_index = (right_index - 1) % len(EFFECTS)
                apply_effect('right', right_index)
            else:
                left_index = (left_index - 1) % len(EFFECTS)
                apply_effect('left', left_index)
            print_status()

    prev_options = options
    prev_l1      = l1
    prev_r1      = r1
    prev_dpad    = dpad
    prev_home    = home


@ds.on_state
def on_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")
    if not connected:
        os._exit(0)


@ds.on_input
def on_input(s):
    update(s)


ds.connect()
print_status()

while True:
    time.sleep(1)
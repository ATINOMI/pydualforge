"""
LED 测试程序
============
操作说明：
  OPTIONS      → 打开/关闭模式菜单
  方向键 上/下  → 在菜单中选择模式
  O            → 确认选择
  PS（Home）键 → 退出程序

── 预设模式 ──
  方向键 上/下  → 切换颜色预设

── 自定义模式 ──
  方向键 上/下  → 选择 R / G / B 通道
  右摇杆 左/右  → 持续调节当前通道值（越偏越快）
  方向键 左/右  → 微调当前通道值（±1）
  X            → 应用颜色

── 彩虹模式 ──
  方向键 上/下  → 切换速度（慢/中/快）
"""

import os
import sys
import time
import threading

os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dualforge import DualForge, DPad

PRESETS = [
    # ── 索尼 / 游戏 ──────────────────────────
    ("索尼蓝      ", (0,    70,  255)),
    ("PS5 白      ", (255, 255,  255)),
    ("马里奥红    ", (228,   0,   15)),
    ("皮卡丘黄    ", (255, 213,    0)),
    ("赛博朋克黄  ", (255, 252,    0)),
    ("传送门蓝    ", (0,   170,  255)),
    ("光晕绿      ", (100, 220,   50)),
    ("暗黑紫      ", (80,    0,  180)),

    # ── 品牌色 ───────────────────────────────
    ("可口可乐红  ", (244,   0,   21)),
    ("耐克橙      ", (245, 128,    0)),
    ("蒂芙尼蓝    ", (10,  186,  181)),
    ("爱马仕橙    ", (229,  93,   34)),
    ("星巴克绿    ", (0,   112,   74)),
    ("法拉利红    ", (204,   0,    0)),
    ("兰博基尼黄  ", (255, 204,    0)),

    # ── 艺术 / 历史 ──────────────────────────
    ("克莱因蓝    ", (0,    47,  167)),
    ("维米尔蓝    ", (31,   73,  125)),
    ("莫奈紫      ", (153,  50,  204)),
    ("中国红      ", (196,   2,   51)),
    ("普鲁士蓝    ", (0,    49,   83)),
    ("玫瑰金      ", (183, 110,   95)),

    # ── 自然 ─────────────────────────────────
    ("极光绿      ", (0,   255,  127)),
    ("极光紫      ", (138,  43,  226)),
    ("日落橙      ", (255, 107,   28)),
    ("深海蓝      ", (0,   105,  148)),
    ("樱花粉      ", (255, 183,  197)),
    ("薰衣草紫    ", (181, 126,  220)),
    ("珊瑚红      ", (255,  87,   51)),
    ("翡翠绿      ", (0,   168,  107)),
    ("沙漠金      ", (194, 154,  108)),
    ("冰川蓝      ", (153, 214,  234)),

    # ── 特殊 ─────────────────────────────────
    ("纯白        ", (255, 255,  255)),
    ("纯黑（关闭）", (0,    0,    0)),
]

# ── 彩虹速度 ──────────────────────────────────────────────────
RAINBOW_SPEEDS = [
    ("慢", 0.05),
    ("中", 0.02),
    ("快", 0.005),
]

# ── 模式定义 ──────────────────────────────────────────────────
MODE_MENU    = 'menu'
MODE_PRESET  = 'preset'
MODE_CUSTOM  = 'custom'
MODE_RAINBOW = 'rainbow'

MODES = [
    (MODE_PRESET,  "预设模式"),
    (MODE_CUSTOM,  "自定义模式"),
    (MODE_RAINBOW, "彩虹模式"),
]

# ── 全局状态 ──────────────────────────────────────────────────
current_mode      = None
menu_open         = False
menu_index        = 0

preset_index      = 0

custom_rgb        = [128, 128, 128]
custom_channel    = 0

rainbow_speed_idx = 1
rainbow_hue       = 0.0
rainbow_thread    = None
rainbow_running   = False

prev_options = False
prev_cross   = False
prev_circle  = False
prev_home    = False
prev_dpad    = DPad.NONE
prev_rx      = 128

ds = DualForge()


# ── 清屏 ──────────────────────────────────────────────────────
def clear():
    os.system('cls' if os.name == 'nt' else 'clear')


# ── 彩虹线程 ──────────────────────────────────────────────────
def hsv_to_rgb(h: float) -> tuple:
    h = h % 1.0
    i = int(h * 6)
    f = h * 6 - i
    q = 1 - f
    t = f
    mapping = [
        (1, t, 0),
        (q, 1, 0),
        (0, 1, t),
        (0, q, 1),
        (t, 0, 1),
        (1, 0, q),
    ]
    r, g, b = mapping[i % 6]
    return int(r * 255), int(g * 255), int(b * 255)


def rainbow_loop():
    global rainbow_hue, rainbow_running
    while rainbow_running:
        speed = RAINBOW_SPEEDS[rainbow_speed_idx][1]
        r, g, b = hsv_to_rgb(rainbow_hue)
        ds.set_led(r, g, b)
        rainbow_hue = (rainbow_hue + 0.005) % 1.0
        time.sleep(speed)


def start_rainbow():
    global rainbow_thread, rainbow_running
    rainbow_running = True
    rainbow_thread = threading.Thread(target=rainbow_loop, daemon=True)
    rainbow_thread.start()


def stop_rainbow():
    global rainbow_running
    rainbow_running = False


# ── 打印函数 ──────────────────────────────────────────────────
def print_header():
    print("=" * 40)
    print("  LED 测试程序")
    print("  OPTIONS → 菜单  |  PS键 → 退出")
    print("=" * 40)


def print_menu():
    clear()
    print_header()
    print("\n╔══ 模式菜单 ══╗")
    for i, (_, name) in enumerate(MODES):
        arrow = " ◀" if i == menu_index else ""
        print(f"║  {i + 1}. {name}{arrow}")
    print("╚══════════════╝")
    print("\n方向键上下选择，O 确认")


def print_preset():
    clear()
    print_header()
    print(f"\n【预设模式】  方向键上下切换\n")
    for i, (name, rgb) in enumerate(PRESETS):
        arrow = " ◀" if i == preset_index else ""
        print(f"  {'▶' if i == preset_index else ' '} {name}  RGB{rgb}{arrow}")


def print_custom():
    clear()
    print_header()
    print(f"\n【自定义模式】")
    print("  方向键上下选通道，左右微调，右摇杆持续调节，X 应用\n")
    channels = ['R', 'G', 'B']
    colors   = ['红', '绿', '蓝']
    for i, (ch, col, val) in enumerate(zip(channels, colors, custom_rgb)):
        arrow  = " ◀" if i == custom_channel else ""
        filled = val // 16
        bar    = '█' * filled + '░' * (16 - filled)
        print(f"  {'▶' if i == custom_channel else ' '} {ch}({col}) [{bar}] {val:3d}{arrow}")
    print(f"\n  预览色：RGB({custom_rgb[0]}, {custom_rgb[1]}, {custom_rgb[2]})")


def print_rainbow():
    clear()
    print_header()
    print(f"\n【彩虹模式】  方向键上下切换速度\n")
    for i, (name, _) in enumerate(RAINBOW_SPEEDS):
        arrow = " ◀" if i == rainbow_speed_idx else ""
        print(f"  {'▶' if i == rainbow_speed_idx else ' '} {name}{arrow}")


def print_standby():
    clear()
    print_header()
    print("\n  待机中（绿色）")
    print("  按 OPTIONS 打开菜单")


# ── 输入处理 ──────────────────────────────────────────────────
def update(s):
    global menu_open, menu_index, current_mode
    global preset_index, custom_channel, custom_rgb
    global rainbow_speed_idx
    global prev_options, prev_cross, prev_circle, prev_home, prev_dpad, prev_rx

    options = s['buttons']['options']
    cross   = s['buttons']['cross']
    circle  = s['buttons']['circle']
    home    = s['buttons']['home']
    dpad    = s['buttons']['dpad']
    rx      = s['sticks']['right']['x']

    # ── PS 键退出 ─────────────────────────────────────────────
    if home and not prev_home:
        clear()
        print("退出程序")
        stop_rainbow()
        ds.set_led(0, 0, 0)
        ds.disconnect()
        os._exit(0)

    # ── OPTIONS 开关菜单 ──────────────────────────────────────
    if options and not prev_options:
        menu_open = not menu_open
        if menu_open:
            stop_rainbow()
            print_menu()
        else:
            if current_mode == MODE_PRESET:
                print_preset()
            elif current_mode == MODE_CUSTOM:
                print_custom()
            elif current_mode == MODE_RAINBOW:
                start_rainbow()
                print_rainbow()
            else:
                print_standby()

    # ── 菜单模式 ──────────────────────────────────────────────
    elif menu_open:
        if dpad == DPad.NORTH and prev_dpad != DPad.NORTH:
            menu_index = (menu_index - 1) % len(MODES)
            print_menu()

        if dpad == DPad.SOUTH and prev_dpad != DPad.SOUTH:
            menu_index = (menu_index + 1) % len(MODES)
            print_menu()

        if circle and not prev_circle:
            stop_rainbow()
            current_mode = MODES[menu_index][0]
            menu_open    = False

            if current_mode == MODE_PRESET:
                r, g, b = PRESETS[preset_index][1]
                ds.set_led(r, g, b)
                print_preset()

            elif current_mode == MODE_CUSTOM:
                print_custom()

            elif current_mode == MODE_RAINBOW:
                start_rainbow()
                print_rainbow()

    # ── 预设模式 ──────────────────────────────────────────────
    elif current_mode == MODE_PRESET:
        if dpad == DPad.NORTH and prev_dpad != DPad.NORTH:
            preset_index = (preset_index - 1) % len(PRESETS)
            r, g, b = PRESETS[preset_index][1]
            ds.set_led(r, g, b)
            print_preset()

        if dpad == DPad.SOUTH and prev_dpad != DPad.SOUTH:
            preset_index = (preset_index + 1) % len(PRESETS)
            r, g, b = PRESETS[preset_index][1]
            ds.set_led(r, g, b)
            print_preset()

    # ── 自定义模式 ────────────────────────────────────────────
    elif current_mode == MODE_CUSTOM:
        changed = False

        if dpad == DPad.NORTH and prev_dpad != DPad.NORTH:
            custom_channel = (custom_channel - 1) % 3
            print_custom()

        if dpad == DPad.SOUTH and prev_dpad != DPad.SOUTH:
            custom_channel = (custom_channel + 1) % 3
            print_custom()

        if dpad == DPad.WEST and prev_dpad != DPad.WEST:
            custom_rgb[custom_channel] = max(0, custom_rgb[custom_channel] - 1)
            changed = True

        if dpad == DPad.EAST and prev_dpad != DPad.EAST:
            custom_rgb[custom_channel] = min(255, custom_rgb[custom_channel] + 1)
            changed = True

        # 右摇杆持续调节
        dead_zone = 20
        center    = 128
        deviation = rx - center
        if abs(deviation) > dead_zone:
            step = int((abs(deviation) - dead_zone) / (127 - dead_zone) * 5) + 1
            if deviation > 0:
                custom_rgb[custom_channel] = min(255, custom_rgb[custom_channel] + step)
            else:
                custom_rgb[custom_channel] = max(0, custom_rgb[custom_channel] - step)
            changed = True

        if changed:
            print_custom()

        if cross and not prev_cross:
            r, g, b = custom_rgb
            ds.set_led(r, g, b)
            print_custom()
            print(f"\n  ✓ 已应用 RGB({r}, {g}, {b})")

    # ── 彩虹模式 ──────────────────────────────────────────────
    elif current_mode == MODE_RAINBOW:
        if dpad == DPad.NORTH and prev_dpad != DPad.NORTH:
            rainbow_speed_idx = (rainbow_speed_idx - 1) % len(RAINBOW_SPEEDS)
            print_rainbow()

        if dpad == DPad.SOUTH and prev_dpad != DPad.SOUTH:
            rainbow_speed_idx = (rainbow_speed_idx + 1) % len(RAINBOW_SPEEDS)
            print_rainbow()

    prev_options = options
    prev_cross   = cross
    prev_circle  = circle
    prev_home    = home
    prev_dpad    = dpad
    prev_rx      = rx


@ds.on_state
def on_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")
    if not connected:
        os._exit(0)


@ds.on_input
def on_input(s):
    update(s)


ds.connect()
ds.set_led(0, 255, 0)
print_standby()

while True:
    time.sleep(1)
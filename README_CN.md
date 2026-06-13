# DualForge

**[English](README.md) | [中文](README_CN.md)**

> PS5 DualSense 控制器的 Python 驱动库。
> 基于 hidapi，支持 Windows / macOS / Linux。

---

## 安装

### 依赖

- Python 3.8+
- hidapi DLL（Windows 需要手动放置 `hidapi.dll`）

```bash
pip install hid
```

### Windows 额外步骤

从 [hidapi releases](https://github.com/libusb/hidapi/releases) 下载 `hidapi-win.zip`，
解压后将 `x64/hidapi.dll` 放到项目根目录。

---

## 快速开始

```python
import os
os.add_dll_directory(os.getcwd())  # Windows 需要，指定 hidapi.dll 路径

from dualforge import DualForge, trigger_effects
import time

ds = DualForge()

@ds.on_state
def on_state(connected):
    print('已连接' if connected else '已断开')

@ds.on_input
def on_input(state):
    if state['buttons']['cross']:
        print('按下了 ✕')
    print(f"左摇杆: {state['sticks']['left']}")
    print(f"电池:   {state['battery']['percent']}%")

ds.connect()

ds.set_led(0, 0, 255)        # 蓝色

ds.set_rumble(200, 200)
time.sleep(1)
ds.stop_rumble()

ds.set_trigger_effect('right', trigger_effects.feedback(3, 5))
time.sleep(3)
ds.set_trigger_effect('right', trigger_effects.off())

ds.disconnect()
```

---

## API 参考

### 连接

```python
ds.connect()       # 连接手柄，找不到设备则抛出 ConnectionError
ds.disconnect()    # 断开连接
ds.is_connected()  # 返回 bool
```

### 事件监听

```python
@ds.on_state
def handle(connected: bool): ...   # 连接状态变化时触发

@ds.on_input
def handle(state: dict): ...       # 每次收到手柄数据时触发
```

### 输入数据结构

```python
state = {
    'sticks': {
        'left':  {'x': 0~255, 'y': 0~255},  # 128 = 居中
        'right': {'x': 0~255, 'y': 0~255},
    },
    'triggers': {
        'left':  0~255,  # 0=未按，255=按到底
        'right': 0~255,
    },
    'buttons': {
        'cross':    bool,
        'square':   bool,
        'circle':   bool,
        'triangle': bool,
        'l1': bool, 'r1': bool,
        'l2': bool, 'r2': bool,
        'l3': bool, 'r3': bool,
        'create':  bool,
        'options': bool,
        'home':    bool,
        'pad':     bool,   # 触摸板点击
        'mute':    bool,
        'dpad':    0~8,    # 见 DPad 枚举
    },
    'gyro': {
        'x': int,  # Pitch，raw int16
        'y': int,  # Roll
        'z': int,  # Yaw
    },
    'accelerometer': {
        'x': int, 'y': int, 'z': int,  # raw int16
    },
    'touch': {
        'finger': [
            {'touching': bool, 'x': 0~1920, 'y': 0~1080},
            {'touching': bool, 'x': 0~1920, 'y': 0~1080},
        ]
    },
    'battery': {
        'percent': 0~100,
        'state':   int,     # 见 PowerState 枚举
    },
    'plugged': {
        'headphones': bool,
        'mic':        bool,
        'mic_muted':  bool,
        'usb_data':   bool,
        'usb_power':  bool,
    },
}
```

### LED 与灯光

```python
ds.set_led(r, g, b)                                      # RGB 灯条，各 0~255
ds.set_player_lights(mask)                               # 玩家指示灯，5位掩码
ds.set_light_brightness(LightBrightness.MID)             # 亮度
ds.set_light_fade_animation(LightFadeAnimation.FADE_IN)  # 淡入淡出
```

玩家指示灯配置：
```python
# Player 1: 0x04  →  - - x - -
# Player 2: 0x06  →  - x - x -
# Player 3: 0x15  →  x - x - x
# Player 4: 0x1B  →  x x - x x
ds.set_player_lights(0x04)
```

### 震动

```python
ds.set_rumble(left, right)  # 各 0~255，left=低频强震，right=高频弱震
ds.stop_rumble()
```

### 扳机 FFB

```python
from dualforge import trigger_effects

# 阻力反馈：position 0~9，strength 1~8
ds.set_trigger_effect('right', trigger_effects.feedback(3, 5))

# 武器触感：start 2~7，end start+1~8，strength 1~8
ds.set_trigger_effect('right', trigger_effects.weapon(2, 6, 8))

# 触发器振动：position 0~9，amplitude 1~8，frequency 1~255 Hz
ds.set_trigger_effect('right', trigger_effects.vibration(0, 5, 20))

# 弓弦张力
ds.set_trigger_effect('right', trigger_effects.bow(2, 6, 5, 4))

# 机枪振动
ds.set_trigger_effect('right', trigger_effects.machine(0, 9, 5, 3, 30, 5))

# 关闭效果
ds.set_trigger_effect('right', trigger_effects.off())
```

### 音频

```python
ds.set_mute_light(MuteLight.BREATHING)  # 静音灯：OFF / ON / BREATHING
ds.set_mic_mute(True)                   # 麦克风静音
ds.set_headphone_volume(80)             # 耳机音量 0~127
ds.set_speaker_volume(50)              # 扬声器音量 0~100
```

### 设备信息

```python
ds.read_mac()          # {'controller_mac': 'XX:XX:XX:XX:XX:XX', 'host_mac': ...}
ds.read_firmware()     # {'firmware_version': '1.16.42', 'hw_generation': 4, ...}
ds.read_calibration()  # 陀螺仪/加速度计校准数据和换算系数
```

---

## 枚举常量

```python
from dualforge import DPad, PowerState, MuteLight, LightBrightness, LightFadeAnimation

DPad.NORTH / NORTHEAST / EAST / SOUTHEAST / SOUTH / SOUTHWEST / WEST / NORTHWEST / NONE

PowerState.DISCHARGING / CHARGING / COMPLETE / ABNORMAL_VOLTAGE / ABNORMAL_TEMPERATURE / CHARGING_ERROR

MuteLight.OFF / ON / BREATHING

LightBrightness.BRIGHT / MID / DIM

LightFadeAnimation.NOTHING / FADE_IN / FADE_OUT
```

---

## 注意事项

- 仅支持 USB 连接，蓝牙模式暂不支持
- Gen4 硬件（第二批次）的玩家指示灯只支持对称配置
- 震动双标志位要求已在库内部处理，无需手动设置
- `ResetLights` 在 `connect()` 时自动发送一次，无需手动处理

---

## 协议参考

- [Game Controller Collective Wiki — DualSense](https://controllers.fandom.com/wiki/Sony_DualSense)
- Vendor ID: `0x054C` / Product ID: `0x0CE6`
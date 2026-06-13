# DualForge

**[English](README.md) | [中文](README_CN.md)**

> A Python driver library for the PS5 DualSense controller.
> Built on hidapi, supports Windows / macOS / Linux.

---

## Installation

### Requirements

- Python 3.8+
- hidapi DLL (Windows requires manual placement of `hidapi.dll`)

```bash
pip install hid
```

### Windows Extra Step

Download `hidapi-win.zip` from [hidapi releases](https://github.com/libusb/hidapi/releases),
extract and place `x64/hidapi.dll` in your project root directory.

---

## Quick Start

```python
import os
os.add_dll_directory(os.getcwd())  # Windows only: specify hidapi.dll path

from dualforge import DualForge, trigger_effects
import time

ds = DualForge()

@ds.on_state
def on_state(connected):
    print('Connected' if connected else 'Disconnected')

@ds.on_input
def on_input(state):
    if state['buttons']['cross']:
        print('Cross button pressed')
    print(f"Left stick: {state['sticks']['left']}")
    print(f"Battery:    {state['battery']['percent']}%")

ds.connect()

ds.set_led(0, 0, 255)        # Blue

ds.set_rumble(200, 200)
time.sleep(1)
ds.stop_rumble()

ds.set_trigger_effect('right', trigger_effects.feedback(3, 5))
time.sleep(3)
ds.set_trigger_effect('right', trigger_effects.off())

ds.disconnect()
```

---

## API Reference

### Connection

```python
ds.connect()       # Connect to controller, raises ConnectionError if not found
ds.disconnect()    # Disconnect
ds.is_connected()  # Returns bool
```

### Event Listeners

```python
@ds.on_state
def handle(connected: bool): ...   # Triggered on connection state change

@ds.on_input
def handle(state: dict): ...       # Triggered on every input report
```

### Input State Structure

```python
state = {
    'sticks': {
        'left':  {'x': 0~255, 'y': 0~255},  # 128 = center
        'right': {'x': 0~255, 'y': 0~255},
    },
    'triggers': {
        'left':  0~255,  # 0=released, 255=fully pressed
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
        'pad':     bool,   # touchpad click
        'mute':    bool,
        'dpad':    0~8,    # see DPad enum
    },
    'gyro': {
        'x': int,  # Pitch, raw int16
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
        'state':   int,    # see PowerState enum
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

### LED & Lights

```python
ds.set_led(r, g, b)                                      # RGB, 0~255 each
ds.set_player_lights(mask)                               # Player indicator lights, 5-bit mask
ds.set_light_brightness(LightBrightness.MID)             # Brightness
ds.set_light_fade_animation(LightFadeAnimation.FADE_IN)  # Fade animation
```

Player light presets:
```python
# Player 1: 0x04  →  - - x - -
# Player 2: 0x06  →  - x - x -
# Player 3: 0x15  →  x - x - x
# Player 4: 0x1B  →  x x - x x
ds.set_player_lights(0x04)
```

### Rumble

```python
ds.set_rumble(left, right)  # 0~255 each, left=low freq, right=high freq
ds.stop_rumble()
```

### Trigger FFB

```python
from dualforge import trigger_effects

# Feedback: position 0~9, strength 1~8
ds.set_trigger_effect('right', trigger_effects.feedback(3, 5))

# Weapon: start 2~7, end start+1~8, strength 1~8
ds.set_trigger_effect('right', trigger_effects.weapon(2, 6, 8))

# Vibration: position 0~9, amplitude 1~8, frequency 1~255 Hz
ds.set_trigger_effect('right', trigger_effects.vibration(0, 5, 20))

# Bow
ds.set_trigger_effect('right', trigger_effects.bow(2, 6, 5, 4))

# Machine
ds.set_trigger_effect('right', trigger_effects.machine(0, 9, 5, 3, 30, 5))

# Off
ds.set_trigger_effect('right', trigger_effects.off())
```

### Audio

```python
ds.set_mute_light(MuteLight.BREATHING)  # OFF / ON / BREATHING
ds.set_mic_mute(True)                   # Mute microphone
ds.set_headphone_volume(80)             # 0~127
ds.set_speaker_volume(50)              # 0~100
```

### Device Info

```python
ds.read_mac()          # {'controller_mac': 'XX:XX:XX:XX:XX:XX', 'host_mac': ...}
ds.read_firmware()     # {'firmware_version': '1.16.42', 'hw_generation': 4, ...}
ds.read_calibration()  # Gyroscope/accelerometer calibration data and conversion factors
```

---

## Enums

```python
from dualforge import DPad, PowerState, MuteLight, LightBrightness, LightFadeAnimation

DPad.NORTH / NORTHEAST / EAST / SOUTHEAST / SOUTH / SOUTHWEST / WEST / NORTHWEST / NONE

PowerState.DISCHARGING / CHARGING / COMPLETE / ABNORMAL_VOLTAGE / ABNORMAL_TEMPERATURE / CHARGING_ERROR

MuteLight.OFF / ON / BREATHING

LightBrightness.BRIGHT / MID / DIM

LightFadeAnimation.NOTHING / FADE_IN / FADE_OUT
```

---

## Notes

- USB only, Bluetooth not supported
- Gen4 hardware (second batch) only supports symmetrical player light configurations
- Rumble dual-flag requirement is handled internally
- `ResetLights` is sent automatically on `connect()`, no manual handling needed

---

## Protocol Reference

- [Game Controller Collective Wiki — DualSense](https://controllers.fandom.com/wiki/Sony_DualSense)
- Vendor ID: `0x054C` / Product ID: `0x0CE6`
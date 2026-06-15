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

## Examples

| File | Description |
|------|-------------|
| `examples/test_trigger_effects.py` | Test all 21 trigger effects interactively |
| `examples/test_led.py` | Test LED with preset / custom / rainbow modes |
| `examples/bow_simulation.py` | Bow simulation using adaptive trigger |

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
def handle(state: dict): ...       # Triggered on every input report (~250Hz)
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

21 effects in total — 7 core effects + 14 presets.

#### Core Effects

```python
from dualforge import trigger_effects

# Off
ds.set_trigger_effect('right', trigger_effects.off())

# Feedback: uniform resistance from position to end
# position 0~9, strength 1~8
ds.set_trigger_effect('right', trigger_effects.feedback(3, 5))

# Weapon: resistance between start and end, releases after
# start 2~7, end start+1~8, strength 1~8
ds.set_trigger_effect('right', trigger_effects.weapon(2, 6, 8))

# Vibration: vibrates from position onward
# position 0~9, amplitude 1~8, frequency 1~255 Hz
ds.set_trigger_effect('right', trigger_effects.vibration(0, 5, 20))

# Bow: like weapon but with snap-back force
# start 0~8, end start+1~8, strength 1~8, snap_force 1~8
ds.set_trigger_effect('right', trigger_effects.bow(0, 7, 7, 6))

# Machine: alternating dual-amplitude vibration
# start 1~8, end start+1~9, amp_a 0~7, amp_b 0~7, frequency 1~255, period 0~255
ds.set_trigger_effect('right', trigger_effects.machine(1, 9, 5, 3, 10, 1))

# Galloping: rhythmic horse-hoof vibration
# start 0~8, end start+1~9, first_foot 0~6, second_foot first_foot+1~7, frequency 1~40
ds.set_trigger_effect('right', trigger_effects.galloping(0, 9, 2, 5, 10))
```

#### Preset Effects

```python
# Resistance presets (based on feedback)
trigger_effects.normal()       # No effect
trigger_effects.very_soft()    # Very light resistance
trigger_effects.soft()         # Light resistance
trigger_effects.medium()       # Medium resistance
trigger_effects.hard()         # Strong resistance
trigger_effects.very_hard()    # Very strong resistance
trigger_effects.hardest()      # Maximum resistance
trigger_effects.rigid()        # Fully locked

# Weapon presets
trigger_effects.game_cube()          # GameCube trigger feel (two-stage)
trigger_effects.semi_automatic_gun() # Semi-auto gun feel
trigger_effects.choppy()             # Choppy resistance (ratchet/gear feel)

# Vibration presets
trigger_effects.automatic_gun()            # Full-auto gun feel
trigger_effects.vibrate_trigger(intensity) # Continuous vibration, intensity 1~255
trigger_effects.vibrate_trigger_pulse()    # Short pulse vibration

# Full custom (direct byte access)
trigger_effects.custom(effect_type, params)  # effect_type + 10 raw bytes
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
- `machine()` start parameter must be >= 1
- All output functions send immediately upon call, no buffering delay

---

## Protocol Reference

- [Game Controller Collective Wiki — DualSense](https://controllers.fandom.com/wiki/Sony_DualSense)
- Vendor ID: `0x054C` / Product ID: `0x0CE6`
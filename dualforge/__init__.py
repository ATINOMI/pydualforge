import os
import time
import threading
os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")

from . import trigger_effects
from . import feature 
from .device import DualSenseDevice
from .input_parser import parse
from .output_builder import OutputBuilder
from . import trigger_effects
from .constants import (
    DPad, PowerState, MuteLight,
    LightBrightness, LightFadeAnimation,
    TriggerEffectType
)


class DualForge:

    def __init__(self):
        self._device  = DualSenseDevice()
        self._output  = OutputBuilder()
        self._running = False
        self._device.add_input_listener(self._on_raw_input)
        self._device.add_state_listener(self._on_state)
        self._input_callbacks  = []
        self._state_callbacks  = []

    def connect(self):
        self._device.connect()
        self._running = True
        self._start_send_loop()
        # 单独发一次 ResetLights，夺取 LED 控制权
        time.sleep(0.5)
        self._send_reset_lights()

    def disconnect(self):
        self._running = False
        self._device.disconnect()

    def is_connected(self) -> bool:
        return self._device.is_connected()

    def on_input(self, fn):
        self._input_callbacks.append(fn)
        return fn

    def on_state(self, fn):
        self._state_callbacks.append(fn)
        return fn

    def set_led(self, r: int, g: int, b: int):
        self._output.set_led(r, g, b)

    def set_rumble(self, left: int, right: int):
        self._output.set_rumble(left, right)

    def stop_rumble(self):
        self._output.stop_rumble()

    def set_trigger_effect(self, target: str, effect_bytes: bytes):
        self._output.set_trigger_effect(target, effect_bytes)

    def set_player_lights(self, mask: int):
        self._output.set_player_lights(mask)

    def set_light_brightness(self, brightness: int):
        self._output.set_light_brightness(brightness)

    def set_light_fade_animation(self, animation: int):
        self._output.set_light_fade_animation(animation)

    def set_mute_light(self, mode: int):
        self._output.set_mute_light(mode)

    def set_mic_mute(self, muted: bool):
        self._output.set_mic_mute(muted)

    def set_headphone_volume(self, volume: int):
        self._output.set_headphone_volume(volume)

    def set_speaker_volume(self, volume: int):
        self._output.set_speaker_volume(volume)

    def read_calibration(self) -> dict:
        return feature.read_calibration(self._device)

    def read_mac(self) -> dict:
        return feature.read_mac(self._device)

    def read_firmware(self) -> dict:
        return feature.read_firmware(self._device)

    def _send_reset_lights(self):
        """单独发一包 ResetLights，不带颜色数据。"""
        report = bytearray(47)
        report[1] |= 0x04  # AllowLedColor
        report[1] |= 0x08  # ResetLights
        self._device.send_report(report)

    def _on_raw_input(self, data: bytes):
        state = parse(data)
        for fn in self._input_callbacks:
            try:
                fn(state)
            except Exception as e:
                print(f"[DualForge] 输入回调异常: {e}")

    def _on_state(self, connected: bool):
        if not connected:
            self._running = False
        for fn in self._state_callbacks:
            try:
                fn(connected)
            except Exception as e:
                print(f"[DualForge] 状态回调异常: {e}")

    def _start_send_loop(self):
        def loop():
            while self._running:
                try:
                    if self._output.is_dirty():
                        report = self._output.build()
                        self._device.send_report(report)
                        self._output.mark_clean()
                except Exception as e:
                    print(f"[DualForge] 发送异常: {e}")
                    break
                time.sleep(1 / 60)

        t = threading.Thread(target=loop, daemon=True)
        t.start()
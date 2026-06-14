import os
import time
import threading
os.add_dll_directory(os.path.dirname(os.path.abspath(__file__)) + "\\..")

from . import trigger_effects
from . import feature
from .device import DualSenseDevice
from .input_parser import parse
from .constants import (
    DPad, PowerState, MuteLight,
    LightBrightness, LightFadeAnimation,
    TriggerEffectType
)

__all__ = ['DualForge', 'trigger_effects', 'feature',
           'DPad', 'PowerState', 'MuteLight',
           'LightBrightness', 'LightFadeAnimation',
           'TriggerEffectType']


class DualForge:

    def __init__(self):
        self._device        = DualSenseDevice()
        self._running       = False
        self._send_lock     = threading.Lock()
        self._led_reset_sent = False
        self._device.add_input_listener(self._on_raw_input)
        self._device.add_state_listener(self._on_state)
        self._input_callbacks = []
        self._state_callbacks = []

    # ── 连接 / 断开 ──────────────────────────────────────────

    def connect(self):
        self._device.connect()
        self._running = True
        time.sleep(0.5)
        self._send_reset_lights()

    def disconnect(self):
        self._running = False
        self._device.disconnect()

    def is_connected(self) -> bool:
        return self._device.is_connected()

    # ── 事件监听 ─────────────────────────────────────────────

    def on_input(self, fn):
        self._input_callbacks.append(fn)
        return fn

    def on_state(self, fn):
        self._state_callbacks.append(fn)
        return fn

    # ── 内部发送 ─────────────────────────────────────────────

    def _send(self, report: bytearray):
        """加锁立刻发送一包报告。"""
        with self._send_lock:
            self._device.send_report(report)

    def _send_reset_lights(self):
        report = bytearray(47)
        report[1] |= 0x04  # AllowLedColor
        report[1] |= 0x08  # ResetLights
        self._led_reset_sent = True
        self._send(report)

    # ── LED ──────────────────────────────────────────────────

    def set_led(self, r: int, g: int, b: int):
        report = bytearray(47)
        report[1] |= 0x04  # AllowLedColor
        if not self._led_reset_sent:
            report[1] |= 0x08
            self._led_reset_sent = True
        report[44] = max(0, min(255, r))
        report[45] = max(0, min(255, g))
        report[46] = max(0, min(255, b))
        self._send(report)

    def set_player_lights(self, mask: int):
        report = bytearray(47)
        report[1] |= 0x10  # AllowPlayerIndicators
        report[43] = mask & 0x1F
        self._send(report)

    def set_light_brightness(self, brightness: int):
        report = bytearray(47)
        report[38] |= 0x01  # AllowLightBrightnessChange
        report[42] = brightness
        self._send(report)

    def set_light_fade_animation(self, animation: int):
        report = bytearray(47)
        report[38] |= 0x02  # AllowColorLightFadeAnimation
        report[41] = animation
        self._send(report)

    # ── 震动 ─────────────────────────────────────────────────

    def set_rumble(self, left: int, right: int):
        report = bytearray(47)
        report[0] |= 0x01  # EnableRumbleEmulation
        report[0] |= 0x02  # UseRumbleNotHaptics
        report[2] = max(0, min(255, right))
        report[3] = max(0, min(255, left))
        self._send(report)

    def stop_rumble(self):
        self.set_rumble(0, 0)

    # ── 扳机 FFB ─────────────────────────────────────────────

    def set_trigger_effect(self, target: str, effect_bytes: bytes):
        report = bytearray(47)
        if target == 'right':
            report[0] |= 0x04  # AllowRightTriggerFFB
            report[10:21] = effect_bytes[:11]
        elif target == 'left':
            report[0] |= 0x08  # AllowLeftTriggerFFB
            report[21:32] = effect_bytes[:11]
        self._send(report)

    # ── 音频 ─────────────────────────────────────────────────

    def set_mute_light(self, mode: int):
        report = bytearray(47)
        report[1] |= 0x01  # AllowMuteLight
        report[8] = mode
        self._send(report)

    def set_mic_mute(self, muted: bool):
        report = bytearray(47)
        report[1] |= 0x02  # AllowAudioMute
        if muted:
            report[9] |= 0x10
        self._send(report)

    def set_headphone_volume(self, volume: int):
        report = bytearray(47)
        report[0] |= 0x10  # AllowHeadphoneVolume
        report[4] = max(0, min(127, volume))
        self._send(report)

    def set_speaker_volume(self, volume: int):
        report = bytearray(47)
        report[0] |= 0x20  # AllowSpeakerVolume
        report[5] = max(0, min(100, volume))
        self._send(report)

    # ── 设备信息 ─────────────────────────────────────────────

    def read_calibration(self) -> dict:
        return feature.read_calibration(self._device)

    def read_mac(self) -> dict:
        return feature.read_mac(self._device)

    def read_firmware(self) -> dict:
        return feature.read_firmware(self._device)

    # ── 内部回调 ─────────────────────────────────────────────

    def _on_raw_input(self, data: bytes):
        from .input_parser import parse
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
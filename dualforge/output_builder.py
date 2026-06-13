from .constants import (
    OutputFlag0, OutputFlag1, OutputFlag38,
    MuteLight, LightBrightness, LightFadeAnimation,
    OUTPUT_REPORT_SIZE
)


class OutputBuilder:

    def __init__(self):
        self._report = bytearray(OUTPUT_REPORT_SIZE)
        self._dirty = False

    def reset(self):
        self._report = bytearray(OUTPUT_REPORT_SIZE)
        self._dirty = False

    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self):
        self._dirty = False

    # ── LED ──────────────────────────────────────────────────

    def set_led(self, r: int, g: int, b: int):
        self._report[1] |= OutputFlag1.ALLOW_LED_COLOR
        self._report[44] = max(0, min(255, r))
        self._report[45] = max(0, min(255, g))
        self._report[46] = max(0, min(255, b))
        self._dirty = True

    def set_player_lights(self, mask: int):
        self._report[1] |= OutputFlag1.ALLOW_PLAYER_INDICATORS
        self._report[43] = mask & 0x1F
        self._dirty = True

    def set_light_brightness(self, brightness: int):
        self._report[38] |= OutputFlag38.ALLOW_LIGHT_BRIGHTNESS
        self._report[42] = brightness
        self._dirty = True

    def set_light_fade_animation(self, animation: int):
        self._report[38] |= OutputFlag38.ALLOW_LIGHT_FADE_ANIMATION
        self._report[41] = animation
        self._dirty = True

    # ── 震动 ─────────────────────────────────────────────────

    def set_rumble(self, left: int, right: int):
        self._report[0] |= OutputFlag0.ENABLE_RUMBLE_EMULATION
        self._report[0] |= OutputFlag0.USE_RUMBLE_NOT_HAPTICS
        self._report[2] = max(0, min(255, right))
        self._report[3] = max(0, min(255, left))
        self._dirty = True

    def stop_rumble(self):
        self.set_rumble(0, 0)

    # ── 扳机 FFB ─────────────────────────────────────────────

    def set_trigger_effect(self, target: str, effect_bytes: bytes):
        if target == 'right':
            self._report[0] |= OutputFlag0.ALLOW_RIGHT_TRIGGER_FFB
            self._report[10:21] = effect_bytes[:11]
        elif target == 'left':
            self._report[0] |= OutputFlag0.ALLOW_LEFT_TRIGGER_FFB
            self._report[21:32] = effect_bytes[:11]
        self._dirty = True

    # ── 音频 ─────────────────────────────────────────────────

    def set_mute_light(self, mode: int):
        self._report[1] |= OutputFlag1.ALLOW_MUTE_LIGHT
        self._report[8] = mode
        self._dirty = True

    def set_mic_mute(self, muted: bool):
        self._report[1] |= OutputFlag1.ALLOW_AUDIO_MUTE
        if muted:
            self._report[9] |= 0x10
        else:
            self._report[9] &= ~0x10
        self._dirty = True

    def set_headphone_volume(self, volume: int):
        self._report[0] |= OutputFlag0.ALLOW_HEADPHONE_VOLUME
        self._report[4] = max(0, min(127, volume))
        self._dirty = True

    def set_speaker_volume(self, volume: int):
        self._report[0] |= OutputFlag0.ALLOW_SPEAKER_VOLUME
        self._report[5] = max(0, min(100, volume))
        self._dirty = True

    # ── 构建 ─────────────────────────────────────────────────

    def build(self) -> bytearray:
        return bytearray(self._report)
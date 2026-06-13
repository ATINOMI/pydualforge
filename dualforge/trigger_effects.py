from .constants import TriggerEffectType


def _make_report() -> bytearray:
    """创建一个空的 11 字节效果缓冲区。"""
    return bytearray(11)


def off() -> bytes:
    """关闭扳机效果。"""
    r = _make_report()
    r[0] = TriggerEffectType.OFF
    return bytes(r)


def feedback(position: int, strength: int) -> bytes:
    """
    阻力反馈：从 position 区域到底部施加均匀阻力。
    position: 0~9
    strength: 1~8
    """
    if not (0 <= position <= 9):
        raise ValueError("position 必须在 0~9 之间")
    if not (1 <= strength <= 8):
        raise ValueError("strength 必须在 1~8 之间")

    r = _make_report()
    force_value  = (strength - 1) & 0x07
    active_zones = 0
    force_zones  = 0

    for i in range(position, 10):
        active_zones |= (1 << i)
        force_zones  |= (force_value << (3 * i))

    r[0] = TriggerEffectType.FEEDBACK
    r[1] = (active_zones >>  0) & 0xFF
    r[2] = (active_zones >>  8) & 0xFF
    r[3] = (force_zones  >>  0) & 0xFF
    r[4] = (force_zones  >>  8) & 0xFF
    r[5] = (force_zones  >> 16) & 0xFF
    r[6] = (force_zones  >> 24) & 0xFF
    return bytes(r)


def weapon(start: int, end: int, strength: int) -> bytes:
    """
    武器触感：在起止区域之间施加阻力，通过后突然释放。
    start:    2~7
    end:      start+1~8
    strength: 1~8
    """
    if not (2 <= start <= 7):
        raise ValueError("start 必须在 2~7 之间")
    if not (start < end <= 8):
        raise ValueError("end 必须在 start+1~8 之间")
    if not (1 <= strength <= 8):
        raise ValueError("strength 必须在 1~8 之间")

    r = _make_report()
    zones = (1 << start) | (1 << end)

    r[0] = TriggerEffectType.WEAPON
    r[1] = (zones >> 0) & 0xFF
    r[2] = (zones >> 8) & 0xFF
    r[3] = (strength - 1) & 0x07
    return bytes(r)


def vibration(position: int, amplitude: int, frequency: int) -> bytes:
    """
    触发器振动：从 position 区域开始振动。
    position:  0~9
    amplitude: 1~8
    frequency: 1~255 Hz
    """
    if not (0 <= position <= 9):
        raise ValueError("position 必须在 0~9 之间")
    if not (1 <= amplitude <= 8):
        raise ValueError("amplitude 必须在 1~8 之间")
    if not (1 <= frequency <= 255):
        raise ValueError("frequency 必须在 1~255 之间")

    r = _make_report()
    strength_value = (amplitude - 1) & 0x07
    active_zones   = 0
    amp_zones      = 0

    for i in range(position, 10):
        active_zones |= (1 << i)
        amp_zones    |= (strength_value << (3 * i))

    r[0] = TriggerEffectType.VIBRATION
    r[1] = (active_zones >>  0) & 0xFF
    r[2] = (active_zones >>  8) & 0xFF
    r[3] = (amp_zones    >>  0) & 0xFF
    r[4] = (amp_zones    >>  8) & 0xFF
    r[5] = (amp_zones    >> 16) & 0xFF
    r[6] = (amp_zones    >> 24) & 0xFF
    r[9] = frequency
    return bytes(r)


def bow(start: int, end: int, strength: int, snap_force: int) -> bytes:
    """
    弓弦张力：类似 weapon，但松开后有回弹力。
    start:      0~8
    end:        start+1~8
    strength:   1~8
    snap_force: 1~8
    """
    if not (0 <= start <= 8):
        raise ValueError("start 必须在 0~8 之间")
    if not (start < end <= 8):
        raise ValueError("end 必须在 start+1~8 之间")
    if not (1 <= strength <= 8):
        raise ValueError("strength 必须在 1~8 之间")
    if not (1 <= snap_force <= 8):
        raise ValueError("snap_force 必须在 1~8 之间")

    r = _make_report()
    zones      = (1 << start) | (1 << end)
    force_pair = (((strength   - 1) & 0x07) << 0) \
               | (((snap_force - 1) & 0x07) << 3)

    r[0] = TriggerEffectType.BOW
    r[1] = (zones      >> 0) & 0xFF
    r[2] = (zones      >> 8) & 0xFF
    r[3] = (force_pair >> 0) & 0xFF
    r[4] = (force_pair >> 8) & 0xFF
    return bytes(r)


def machine(start: int, end: int,
            amp_a: int, amp_b: int,
            frequency: int, period: int) -> bytes:
    """
    机枪振动：双振幅交替振动。
    start:     0~8
    end:       start+1~9
    amp_a:     0~7  主振幅
    amp_b:     0~7  副振幅
    frequency: 1~255 Hz
    period:    0~255（单位：1/10秒）
    """
    if not (0 <= start <= 8):
        raise ValueError("start 必须在 0~8 之间")
    if not (start < end <= 9):
        raise ValueError("end 必须在 start+1~9 之间")
    if not (0 <= amp_a <= 7):
        raise ValueError("amp_a 必须在 0~7 之间")
    if not (0 <= amp_b <= 7):
        raise ValueError("amp_b 必须在 0~7 之间")
    if not (1 <= frequency <= 255):
        raise ValueError("frequency 必须在 1~255 之间")

    r = _make_report()
    zones         = (1 << start) | (1 << end)
    strength_pair = ((amp_a & 0x07) << 0) | ((amp_b & 0x07) << 3)

    r[0] = TriggerEffectType.MACHINE
    r[1] = (zones         >> 0) & 0xFF
    r[2] = (zones         >> 8) & 0xFF
    r[3] = (strength_pair >> 0) & 0xFF
    r[4] = frequency
    r[5] = period
    return bytes(r)
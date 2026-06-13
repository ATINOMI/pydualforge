from .constants import DPad, PowerState

def parse(data:bytes) -> dict:
    """
    把 63 字节的输入报告解析成结构化字典
    data: 不含 Report ID 的 63 字节原始数据
    """

    # ── 工具函数 ──────────────────────────────────────────────
    def u8(offset):
        """读取一个无符号字节"""
        return data[offset]
    
    def i16(offset):
        """读取一个有符号16位整数（小端序）"""
        val = data[offset] | (data[offset + 1] << 8)
        if val >= 0x8000:
            val -= 0x10000
        return
    
    def u32(offset):
        """读取一个无符号32位整数（小端序）"""
        return   (data[offset]
                | data[offset + 1] << 8
                | data[offset + 2] << 16
                | data[offset + 3] << 24)
    
    # ── 字节 7：方向键 + 四个按键 ─────────────────────────────
    byte7    = u8(7)
    dpad_raw = byte7 & 0x0F

    # ── 字节 8：肩键 ──────────────────────────────────────────
    byte8 = u8(8)

    # ── 字节 9：系统键 ────────────────────────────────────────
    byte9 = u8(9)

    # ── 触摸板手指解析 ────────────────────────────────────────
    def parse_finger(offset):
        raw = u32(offset)
        return {
            'touching': not bool((raw >> 7) & 1),
            'x': (raw >> 8)  & 0xFFF,
            'y': (raw >> 20) & 0xFFF,
        }
    
    # ── 字节 52：电源 ─────────────────────────────────────────
    byte52 = u8(52)

    # ── 字节 53：插入状态 ─────────────────────────────────────
    byte53 = u8(53)

    return{
        # 摇杆（0~255，128=居中）
        'sticks': {
            'left':  {'x': u8(0), 'y': u8(1)},
            'right': {'x': u8(2), 'y': u8(3)},
        },

        # 扳机（0~255）
        'triggers': {
            'left':  u8(4),
            'right': u8(5),
        },

        # 按键
        'buttons': {
            'dpad':     dpad_raw,          # 用 DPad 枚举对比
            'square':   bool((byte7 >> 4) & 1),
            'cross':    bool((byte7 >> 5) & 1),
            'circle':   bool((byte7 >> 6) & 1),
            'triangle': bool((byte7 >> 7) & 1),
            'l1':       bool((byte8 >> 0) & 1),
            'r1':       bool((byte8 >> 1) & 1),
            'l2':       bool((byte8 >> 2) & 1),
            'r2':       bool((byte8 >> 3) & 1),
            'create':   bool((byte8 >> 4) & 1),
            'options':  bool((byte8 >> 5) & 1),
            'l3':       bool((byte8 >> 6) & 1),
            'r3':       bool((byte8 >> 7) & 1),
            'home':     bool((byte9 >> 0) & 1),
            'pad':      bool((byte9 >> 1) & 1),
            'mute':     bool((byte9 >> 2) & 1),
        },  

        # IMU 传感器
        'gyro': {
            'x': i16(15),
            'y': i16(17),
            'z': i16(19),
        },
        'accelerometer': {
            'x': i16(21),
            'y': i16(23),
            'z': i16(25),
        },

        # 触摸板
        'touch': {
            'finger': [
                parse_finger(32),
                parse_finger(36),
            ]
        },


        # 扳机 FFB 状态反馈
        'trigger_feedback': {
            'right': {
                'stop_location': u8(41) & 0x0F,
                'status':        (u8(41) >> 4) & 0x0F,
                'effect':        u8(47) & 0x0F,
            },
            'left': {
                'stop_location': u8(42) & 0x0F,
                'status':        (u8(42) >> 4) & 0x0F,
                'effect':        (u8(47) >> 4) & 0x0F,
            },
        },

        # 电源
        'battery': {
            'percent': (byte52 & 0x0F) * 10,  # 0~10 → 0%~100%
            'state':   (byte52 >> 4) & 0x0F,  # 用 PowerState 枚举对比
        },

        # 插入状态
        'plugged': {
            'headphones': bool((byte53 >> 0) & 1),
            'mic':        bool((byte53 >> 1) & 1),
            'mic_muted':  bool((byte53 >> 2) & 1),
            'usb_data':   bool((byte53 >> 3) & 1),
            'usb_power':  bool((byte53 >> 4) & 1),
        },
    }
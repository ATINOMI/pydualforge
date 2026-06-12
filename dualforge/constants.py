# DualSense USB 设备标识
VENDOR_ID  = 0x054C
PRODUCT_ID = 0x0CE6

# Report ID
REPORT_ID_INPUT   = 0x01  # 输入报告（手柄 → 电脑）
REPORT_ID_OUTPUT  = 0x02  # 输出报告（电脑 → 手柄）
REPORT_ID_CALIB   = 0x05  # Feature：校准数据
REPORT_ID_MAC     = 0x09  # Feature：MAC 地址
REPORT_ID_FIRMWARE = 0x20 # Feature：固件版本

# 输出报告大小
OUTPUT_REPORT_SIZE = 47

# 输入报告大小（不含 Report ID）
INPUT_REPORT_SIZE = 63

# 方向键枚举
class DPad:
    NORTH     = 0
    NORTHEAST = 1
    EAST      = 2
    SOUTHEAST = 3
    SOUTH     = 4
    SOUTHWEST = 5
    WEST      = 6
    NORTHWEST = 7
    NONE      = 8

# 电源状态枚举
class PowerState:
    DISCHARGING          = 0x00
    CHARGING             = 0x01
    COMPLETE             = 0x02
    ABNORMAL_VOLTAGE     = 0x0A
    ABNORMAL_TEMPERATURE = 0x0B
    CHARGING_ERROR       = 0x0F

# 静音灯枚举
class MuteLight:
    OFF       = 0
    ON        = 1
    BREATHING = 2

# 亮度枚举
class LightBrightness:
    BRIGHT = 0
    MID    = 1
    DIM    = 2

# 淡入淡出动画枚举
class LightFadeAnimation:
    NOTHING  = 0
    FADE_IN  = 1
    FADE_OUT = 2

# 触发器 FFB 效果类型
class TriggerEffectType:
    OFF        = 0x05
    FEEDBACK   = 0x21
    WEAPON     = 0x25
    VIBRATION  = 0x26
    BOW        = 0x22
    GALLOPING  = 0x23
    MACHINE    = 0x27

# 输出报告标志位（字节 0）
class OutputFlag0:
    ENABLE_RUMBLE_EMULATION = 0x01
    USE_RUMBLE_NOT_HAPTICS  = 0x02
    ALLOW_RIGHT_TRIGGER_FFB = 0x04
    ALLOW_LEFT_TRIGGER_FFB  = 0x08
    ALLOW_HEADPHONE_VOLUME  = 0x10
    ALLOW_SPEAKER_VOLUME    = 0x20
    ALLOW_MIC_VOLUME        = 0x40
    ALLOW_AUDIO_CONTROL     = 0x80

# 输出报告标志位（字节 1）
class OutputFlag1:
    ALLOW_MUTE_LIGHT        = 0x01
    ALLOW_AUDIO_MUTE        = 0x02
    ALLOW_LED_COLOR         = 0x04
    RESET_LIGHTS            = 0x08
    ALLOW_PLAYER_INDICATORS = 0x10

# 输出报告标志位（字节 38）
class OutputFlag38:
    ALLOW_LIGHT_BRIGHTNESS       = 0x01
    ALLOW_LIGHT_FADE_ANIMATION   = 0x02
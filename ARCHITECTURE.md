# DualForge 库架构文档

> 本文档描述 DualForge 库的内部架构、数据流和关键机制。

---

## 目录

1. [文件结构](#1-文件结构)
2. [整体架构](#2-整体架构)
3. [数据流](#3-数据流)
4. [注册机制（回调）](#4-注册机制回调)
5. [线程模型](#5-线程模型)
6. [各模块职责](#6-各模块职责)

---

## 1. 文件结构

```
dualforge/
├── __init__.py        ← 用户入口，DualForge 主类
├── device.py          ← 底层 HID 设备管理
├── input_parser.py    ← 输入报告解析（63字节 → 字典）
├── output_builder.py  ← 输出报告构造（备用，当前未使用）
├── trigger_effects.py ← 扳机 FFB 效果工厂函数
├── feature.py         ← Feature Report 读取
└── constants.py       ← 枚举和魔法数字
```

---

## 2. 整体架构

```
用户代码（示例程序）
        ↕  调用 API / 接收回调
    DualForge（__init__.py）
        ↕  发送报告 / 接收原始数据
    DualSenseDevice（device.py）
        ↕  HID 读写
    hidapi（系统库）
        ↕  USB 总线
    DualSense 手柄
```

每一层只和相邻层通信，用户不需要知道底层细节。

---

## 3. 数据流

### 输入数据流（手柄 → 用户）

```
手柄发送原始字节（每 1ms 一次）
        ↓
device.py 的 _read_loop() 读取 64 字节
        ↓ 去掉第一个字节（Report ID = 0x01）
63 字节原始数据
        ↓ _notify_input(payload)
__init__.py 的 _on_raw_input(data)
        ↓ input_parser.parse(data)
结构化字典 state = {
    'buttons': {'cross': False, ...},
    'sticks':  {'left': {'x': 128, 'y': 128}},
    'triggers': {'left': 0, 'right': 0},
    'gyro':    {'x': 0, 'y': 0, 'z': 0},
    'battery': {'percent': 80, 'state': 0},
    ...
}
        ↓ fn(state)
用户的 on_input(s) 被调用
```

### 输出数据流（用户 → 手柄）

```
用户调用 ds.set_trigger_effect('right', effect)
        ↓
__init__.py 构建 47 字节报告
        ↓ _send(report)
加锁（_send_lock）
        ↓
device.py 的 send_report(data)
        ↓ bytes([0x02]) + data（加上 Report ID）
hidapi 的 device.write(48字节)
        ↓ USB 总线
手柄接收并执行
```

---

## 4. 注册机制（回调）

DualForge 使用两层注册机制：

### 第一层：device.py 的监听器

```python
# device.py 内部
self._input_listeners = []   # 存放监听器函数的列表
self._state_listeners = []

def add_input_listener(self, fn):
    self._input_listeners.append(fn)  # 注册：把函数加进列表

def _notify_input(self, data):
    for fn in self._input_listeners:
        fn(data)                       # 触发：逐个调用
```

**注册者：** `__init__.py` 在初始化时注册：
```python
self._device.add_input_listener(self._on_raw_input)
self._device.add_state_listener(self._on_state)
```

### 第二层：DualForge 的回调

```python
# __init__.py 内部
self._input_callbacks = []   # 存放用户回调的列表

def on_input(self, fn):
    self._input_callbacks.append(fn)  # 注册
    return fn                          # 支持装饰器语法

def _on_raw_input(self, data):
    state = parse(data)
    for fn in self._input_callbacks:
        fn(state)                      # 触发
```

**注册者：** 用户在示例程序里注册：
```python
@ds.on_input           # 等价于 ds.on_input(on_input)
def on_input(s):
    update(s)
```

### 两层的关系

```
device.py 的 _input_listeners
    存放的是 → __init__.py 的 _on_raw_input

__init__.py 的 _input_callbacks
    存放的是 → 用户的 on_input(s)
```

为什么要两层？因为中间需要做一次数据转换：

```
device.py 传出：63 字节原始数据（bytes）
                    ↓ parse() 转换
__init__.py 传给用户：结构化字典（dict）
```

---

## 5. 线程模型

DualForge 运行时有两个线程：

```
主线程                          后台读取线程（daemon）
─────────────────               ──────────────────────
ds.connect()          →  →  →  启动
ds.set_led()                    _read_loop() 持续运行
ds.set_rumble()                     ↓ 读到数据
time.sleep()                    _notify_input()
ds.disconnect()                     ↓ 调用 _on_raw_input
                                _on_raw_input()
                                    ↓ parse()
                                调用用户的 on_input(s)
                                    ↓ update(s)
                                set_trigger_effect()  ← 这里也在写设备！
```

### 线程安全问题

后台线程的回调链最终会调用 `set_trigger_effect()`，而主线程也可能同时调用 `set_led()`，两个线程同时写 HID 设备会报错：

```
重叠 I/O 事件不在信号状态中
```

### 解决方案：锁

```python
self._send_lock = threading.Lock()

def _send(self, report):
    with self._send_lock:        # 拿锁
        self._device.send_report(report)
                                 # 自动释放锁
```

任何线程写设备前必须先拿锁，保证同一时间只有一个线程在写。

### 守护线程

```python
t = threading.Thread(target=self._read_loop, daemon=True)
```

`daemon=True` 意味着主程序退出时，后台线程自动跟着退出，不会让程序卡住。

---

## 6. 各模块职责

### `device.py` — 底层 HID 管理

职责：
- 枚举并连接 DualSense 设备（VID=0x054C, PID=0x0CE6）
- 启动后台读取线程
- 提供 `send_report()` 和 `get_feature_report()` 接口
- 管理监听器数组（输入监听器、状态监听器）

不负责：
- 数据解析
- 报告构造
- 业务逻辑

### `input_parser.py` — 输入报告解析

职责：
- 把 63 字节原始数据解析成结构化字典
- 处理位域提取（方向键、按键）
- 处理有符号整数（陀螺仪、加速度计）
- 处理触摸板坐标（12位位域）

关键注意事项：
- 陀螺仪轴顺序是 X/Z/Y，不是 X/Y/Z
- 触摸板每根手指是 32 位位域，小端序
- 电源百分比是 0~10，需要乘以 10 转换为百分比

### `trigger_effects.py` — FFB 效果工厂

职责：
- 提供各种扳机效果的构造函数
- 返回 11 字节的效果数据

效果类型：

| 函数 | 效果类型 | 说明 |
|------|---------|------|
| `off()` | 0x05 | 关闭效果 |
| `feedback(position, strength)` | 0x21 | 线性阻力 |
| `weapon(start, end, strength)` | 0x25 | 武器触感 |
| `vibration(position, amplitude, frequency)` | 0x26 | 振动 |
| `bow(start, end, strength, snap_force)` | 0x22 | 弓弦张力 |
| `machine(start, end, amp_a, amp_b, freq, period)` | 0x27 | 机枪振动 |

### `feature.py` — Feature Report 读取

职责：
- 读取陀螺仪/加速度计校准数据（Report 0x05）
- 读取 MAC 地址（Report 0x09）
- 读取固件版本和硬件信息（Report 0x20）

注意：Feature Report 返回的数据**包含 Report ID 在字节0**，解析时偏移量从 1 开始。

### `constants.py` — 枚举和常量

职责：
- 集中管理所有魔法数字
- 定义枚举类（DPad、PowerState、MuteLight 等）
- 定义标志位常量（OutputFlag0、OutputFlag1 等）

### `__init__.py` — 用户入口

职责：
- 封装 `DualSenseDevice` 和各功能模块
- 提供简洁的用户 API
- 管理用户回调列表
- 处理 `ResetLights` 时序（连接后单独发一次）
- 提供即时发送模式（每个函数各自构建报告立刻发送）

---

## 关键设计决策记录

### 1. 即时发送模式 vs 状态机模式

**最终选择：即时发送模式**

原因：状态机模式有发送延迟（最多 16ms），对扳机 FFB 的实时性影响明显。即时发送模式每次调用立刻发出报告，延迟最小。

代价：`set_led()` 和 `set_rumble()` 各自发独立的报告，但由于标志位机制，互不干扰。

### 2. ResetLights 单独发送

DualSense 在 USB 模式下 LED 控制权在固件手里，需要发送 `ResetLights` 信号夺取控制权。

此信号必须单独发一包空报告（不带颜色数据），连接后延迟 500ms 发送一次，之后不再发送。

### 3. 震动双标志位

震动必须同时设置两个标志位：
```python
report[0] |= 0x01  # EnableRumbleEmulation
report[0] |= 0x02  # UseRumbleNotHaptics
```

只设其中一个，马达不响应。

---

*文档版本：v1.0 | 基于 DualForge v0.1.0*

# pydualforge 性能分析报告

**分析时间：** 2026-06-15  
**分析范围：** `dualforge/` 核心模块 + `examples/`  
**代码版本：** `55820f6`

---

## 摘要

| 等级 | 数量 |
|------|------|
| 🔴 高优先级（热路径） | 2 |
| 🟠 中优先级 | 1 |
| 🟡 低优先级（冷路径） | 1 |

> DualSense USB 模式输入频率约 **250Hz**，即每 4ms 触发一次输入回调。性能分析以此为基准。

---

## 🔴 高优先级

### P-01 · `parse()` 每帧重建内嵌函数闭包

**文件：** [`dualforge/input_parser.py`](dualforge/input_parser.py)，第 10–45 行  
**触发频率：** 250 次/秒

`parse()` 内部定义了 4 个函数：

```python
def parse(data: bytes) -> dict:
    def u8(offset): ...          # ← 每次调用 parse() 都重新创建
    def i16(offset): ...         # ← 每次调用 parse() 都重新创建
    def u32(offset): ...         # ← 每次调用 parse() 都重新创建
    def parse_finger(offset): ...# ← 每次调用 parse() 都重新创建
```

每次 `parse()` 被调用时，Python 都会为这 4 个函数分别创建函数对象和对应的闭包（捕获 `data`），每秒产生 **1000 个短命函数对象**，给 GC 持续施压。

**修复：** 将 `u8`/`u32` 提到模块级别（不捕获 `data`，改为接收参数）；`i16` 和 `parse_finger` 同理：

```python
# 模块级别，无闭包开销
def _u8(data, offset):
    return data[offset]

def _i16(data, offset):
    val = data[offset] | (data[offset + 1] << 8)
    return val - 0x10000 if val >= 0x8000 else val

def _u32(data, offset):
    return (data[offset]
          | data[offset + 1] << 8
          | data[offset + 2] << 16
          | data[offset + 3] << 24)

def _parse_finger(data, offset):
    raw = _u32(data, offset)
    return {
        'touching': not bool((raw >> 7) & 1),
        'x': (raw >> 8)  & 0xFFF,
        'y': (raw >> 20) & 0xFFF,
    }

def parse(data: bytes) -> dict:
    ...
```

---

### P-02 · `parse()` 每帧分配大量嵌套字典

**文件：** [`dualforge/input_parser.py`](dualforge/input_parser.py)，第 53–135 行  
**触发频率：** 250 次/秒

每次 `parse()` 返回一个包含约 **10 个嵌套 dict** 的结构：

```
顶层 dict
├── sticks      → dict(left=dict, right=dict)
├── triggers    → dict
├── buttons     → dict（15 个键）
├── gyro        → dict
├── accelerometer → dict
├── touch       → dict(finger=[dict, dict])
├── trigger_feedback → dict(right=dict, left=dict)
├── battery     → dict
└── plugged     → dict
```

每秒产生约 **2500 个短命 dict 对象**，内存分配和 GC 回收开销随应用运行时间累积。

**修复方向（按成本排序）：**

**方案 A（低成本）：** 改用 `__slots__` dataclass，减少每个对象的内存占用：
```python
from dataclasses import dataclass

@dataclass(slots=True)
class StickState:
    x: int
    y: int

@dataclass(slots=True)
class InputState:
    sticks_left: StickState
    sticks_right: StickState
    trigger_left: int
    trigger_right: int
    ...
```

**方案 B（高成本，最优）：** 预分配一个可复用的状态对象，`parse()` 改为 `parse_into(data, state)` 原地更新，彻底消除每帧的堆分配。

---

## 🟠 中优先级

### P-03 · 输出 API 每次调用都分配 `bytearray(47)`

**文件：** [`dualforge/__init__.py`](dualforge/__init__.py)，第 75–155 行  
**触发频率：** 取决于用户调用频率

`set_led()`、`set_rumble()`、`set_trigger_effect()` 等所有输出方法的模式都是：

```python
def set_led(self, r, g, b):
    report = bytearray(47)   # ← 每次调用都分配新对象
    ...
    self._send(report)
```

在 `bow_simulation.py` 示例中，`set_led()` 在每帧回调里被调用，即 250 次/秒，每秒产生 250 个 47 字节的短命 bytearray。

**修复：** 在 `DualForge.__init__` 中预分配缓冲区，发送前在锁内清零复用：

```python
def __init__(self):
    ...
    self._report_buf = bytearray(47)

def set_led(self, r: int, g: int, b: int):
    with self._send_lock:
        buf = self._report_buf
        buf[:] = b'\x00' * 47       # 清零
        buf[1] |= 0x04
        buf[44] = max(0, min(255, r))
        buf[45] = max(0, min(255, g))
        buf[46] = max(0, min(255, b))
        self._device.send_report(buf)
```

---

## 🟡 低优先级

### P-04 · `feedback()`/`vibration()` 使用循环计算可用位运算替代

**文件：** [`dualforge/trigger_effects.py`](dualforge/trigger_effects.py)，第 32–34 行、第 89–91 行  
**触发频率：** 极低（仅在设置效果时调用一次）

```python
for i in range(position, 10):
    active_zones |= (1 << i)
    force_zones  |= (force_value << (3 * i))
```

`active_zones` 可以用位运算一步算出，避免循环：

```python
# 等价于对 position~9 的所有位置位
active_zones = ((1 << (10 - position)) - 1) << position
```

`force_zones`（每 3 bit 一组重复填充 `force_value`）可用整数乘法技巧：

```python
# 在 10 个 3-bit 槽中填充同一个值，掩码取低 30 bit
MASK_30 = (1 << 30) - 1
repeater = sum(1 << (3 * i) for i in range(10))   # 模块级预计算常量
force_zones = (force_value * repeater) & MASK_30
# 再按 active_zones 掩码取有效区域
force_zones &= active_zones * 0b111   # 展开有效槽
```

> 注意：此处属于冷路径优化，实际性能收益极小，**仅在代码整洁性上有价值**，不建议优先处理。

---

## 优先级汇总

| ID | 文件 | 问题 | 频率 | 优先级 |
|----|------|------|------|--------|
| P-01 | `input_parser.py` | 每帧重建 4 个闭包函数 | 250Hz | 🔴 高 |
| P-02 | `input_parser.py` | 每帧分配 10+ 嵌套 dict | 250Hz | 🔴 高 |
| P-03 | `__init__.py` | 每次输出调用分配 `bytearray(47)` | 用户频率 | 🟠 中 |
| P-04 | `trigger_effects.py` | 循环计算可改位运算 | 极低（一次性） | 🟡 低 |

**建议处理顺序：** P-01 → P-02（合并修改 `input_parser.py`）→ P-03 → P-04 可跳过。

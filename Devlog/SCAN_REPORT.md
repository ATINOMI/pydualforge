# pydualforge 代码扫描报告

**扫描时间：** 2026-06-15  
**扫描范围：** `dualforge/` 核心模块 + `examples/`  
**代码版本：** `55820f6`（从状态机模式改成即时发生模式，示例程序编写）

---

## 摘要

| 等级 | 数量 |
|------|------|
| 🔴 Bug（功能破坏） | 1 |
| 🟠 质量问题 | 3 |
| 🟡 设计建议 | 2 |

---

## 🔴 Bug

### B-01 · `i16()` 缺少 `return` 语句

**文件：** [`dualforge/input_parser.py`](dualforge/input_parser.py)，第 14–19 行  
**严重程度：** 高——静默失效，不抛出异常但数据全部错误

**问题代码：**
```python
def i16(offset):
    val = data[offset] | (data[offset + 1] << 8)
    if val >= 0x8000:
        val -= 0x10000
    return        # ← 应为 return val
```

**影响范围：**  
所有依赖 `i16()` 的字段均返回 `None`：
- `state['gyro']['x/y/z']`
- `state['accelerometer']['x/y/z']`

以及 [`dualforge/feature.py`](dualforge/feature.py) 中 `read_calibration()` 的独立 `i16()` 实现**没有此问题**（两处实现不共享）。

**修复：**
```python
def i16(offset):
    val = data[offset] | (data[offset + 1] << 8)
    if val >= 0x8000:
        val -= 0x10000
    return val
```

---

## 🟠 质量问题

### Q-01 · `except Exception` 吞掉所有错误信息

**文件：** [`dualforge/device.py`](dualforge/device.py)，第 64–76 行

```python
except Exception:          # 出了什么错完全不知道
    if self._running:
        self._running = False
        self._device  = None
        self._notify_state(False)
    break
```

后台读取线程异常时，控制台无任何输出，用户无法判断是 USB 断开、权限拒绝还是数据格式错误。

**修复：**
```python
except Exception as e:
    if self._running:
        print(f"[DualSense] 读取线程异常: {e}")
        self._running = False
        self._device  = None
        self._notify_state(False)
    break
```

---

### Q-02 · `_on_raw_input` 内重复导入 `parse`

**文件：** [`dualforge/__init__.py`](dualforge/__init__.py)，第 9 行 vs 第 170 行

文件顶部已有：
```python
from .input_parser import parse   # 第 9 行
```

方法内部又重复：
```python
def _on_raw_input(self, data: bytes):
    from .input_parser import parse   # 第 170 行，冗余
    state = parse(data)
```

虽然 Python 模块系统有缓存不会重复执行，但代码造成误解（像是刻意延迟导入，实则无必要）。删去方法内的 `import` 即可。

---

### Q-03 · `import math` 写在函数内部

**文件：** [`dualforge/feature.py`](dualforge/feature.py)，第 39 行

```python
def read_calibration(device) -> dict:
    ...
    import math          # ← 应移至文件顶部
    DEG2RAD = math.pi / 180.0
```

每次调用 `read_calibration()` 都会触发一次 `import` 语句（即使有缓存）。标准做法是将 `import math` 和常量 `DEG2RAD = math.pi / 180.0` 移至模块顶层。

---

## 🟡 设计建议

### D-01 · `GALLOPING` 效果缺少实现

**文件：** [`dualforge/constants.py`](dualforge/constants.py)，第 63 行；[`dualforge/trigger_effects.py`](dualforge/trigger_effects.py)

`constants.py` 中已定义：
```python
class TriggerEffectType:
    ...
    GALLOPING = 0x23
```

但 `trigger_effects.py` 中没有对应的 `galloping()` 函数，导致 API 不完整——用户看到常量定义后会期待有配套函数。建议补充实现或在常量旁加注说明该效果暂未实现。

---

### D-02 · 枚举类未使用 `enum.IntEnum`

**文件：** [`dualforge/constants.py`](dualforge/constants.py)

当前所有枚举（`DPad`、`PowerState`、`MuteLight` 等）均用普通类存整数常量：

```python
class DPad:
    NORTH     = 0
    NORTHEAST = 1
    ...
```

问题：
- 传入任意整数不会报错，类型安全性为零
- 无法迭代、无法通过值反查名称（调试困难）
- `isinstance()` 检查无意义

建议改为 `enum.IntEnum`，兼容现有整数比较逻辑的同时获得类型检查：

```python
from enum import IntEnum

class DPad(IntEnum):
    NORTH     = 0
    NORTHEAST = 1
    ...
```

---

## 附：文件覆盖情况

| 文件 | 行数 | 扫描结果 |
|------|------|----------|
| `dualforge/constants.py` | 89 | D-02 |
| `dualforge/input_parser.py` | 135 | **B-01** |
| `dualforge/trigger_effects.py` | 167 | D-01 |
| `dualforge/feature.py` | 154 | Q-03 |
| `dualforge/device.py` | 113 | Q-01 |
| `dualforge/__init__.py` | 184 | Q-02 |
| `examples/bow_simulation.py` | 133 | 无问题 |

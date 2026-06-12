import os
os.add_dll_directory(os.getcwd())

from dualforge.device import DualSenseDevice
import time

def on_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")

def on_input(data):
    # 只打印前10个字节看看
    print(f"收到数据: {list(data[:10])}")

ds = DualSenseDevice()
ds.add_state_listener(on_state)
ds.add_input_listener(on_input)
ds.connect()

# 保持运行5秒
time.sleep(5)
ds.disconnect()
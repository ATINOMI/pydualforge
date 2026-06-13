import os
os.add_dll_directory(os.getcwd())

from dualforge import DualForge
import time

ds = DualForge()

@ds.on_state
def handle_state(connected):
    print(f"连接状态: {'已连接' if connected else '已断开'}")

ds.connect()
time.sleep(0.5)

print("── MAC 地址 ──")
print(ds.read_mac())

print("── 固件信息 ──")
print(ds.read_firmware())

print("── 校准数据 ──")
print(ds.read_calibration())

time.sleep(1)
ds.disconnect()
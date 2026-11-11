# Pico 发送端准备

[English](README.md) · [裸机入口](../README.zh-CN.md) · [接线](../docs/hardware.zh-CN.md)

使用 RP2040 Raspberry Pi Pico。发送固件为 `zve10_uart_od 15`，
包含 PIO/DMA 串口发送、开漏输出和 GP27 复位。

## 构建与安装

需要 `arduino-cli` 和 Arduino-Pico 的 `rp2040:rp2040` core（本次构建使用 6.3.0）。
在 `fastboot/` 目录执行：

```sh
arduino-cli compile --fqbn rp2040:rp2040:rpipico \
  --build-property build.extra_flags=-DOPEN_DRAIN \
  --output-dir pico/build-v15-rp2040 pico/firmware/zve10_pico_od_reset
arduino-cli compile --fqbn rp2040:rp2040:rpipico2 \
  --build-property build.extra_flags=-DOPEN_DRAIN \
  --output-dir pico/build-v15-rp2350 pico/firmware/zve10_pico_od_reset
```

编译得到 UF2 后，按住 Pico 的 BOOTSEL 接入 USB，将 UF2 拷入出现的 `RPI-RP2` 磁盘。
固件目录里的 `serialboot.pio.h` 是与 `.pio` 对应、构建所需的源代码头文件，应一起保留。

生产默认复位脉冲为 10 us。有界的 10 us 至 100 ms 诊断使用
`reset_only.py --pulse-us`；注入始终保留默认值。本地 UF2 保存在忽略的
`pico/build-v*/` 目录。

### 两块 Pico 的安全部署

Linux 的 `/dev/ttyACM*` 编号会在重连后交换。命令应使用稳定的
`/dev/serial/by-id/` 链接。安装 UF2 前，拔掉另一块 Pico，手动进入 BOOTSEL，
并确认只有一个启动盘：

- RP2040 发送器：USB ID `2e8a:0003`，卷标 `RPI-RP2`，使用 RP2040 UF2；
- RP2350 Pico 2：USB ID `2e8a:000f`，卷标 `RP2350`，使用 RP2350 UF2。

两个启动盘同时存在时，不要让自动上传器选盘。只有核对 USB ID 和卷标后，
才复制对应的 UF2。

## 检查与使用

```sh
.venv/bin/python pico/inspect_pico.py --port /dev/cu.usbmodemXXXX
.venv/bin/python pico/inject_payload.py --port /dev/cu.usbmodemXXXX \
  --file prebuilt/stage1.bin --duration 15 --record-gap 0.002 --countdown 5
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5 --pulses 5 --interval 1
.venv/bin/python pico/reset_only.py --port /dev/cu.usbmodemXXXX \
  --countdown 5 --pulse-us 10000
.venv/bin/python pico/monitor_line.py --port /dev/cu.usbmodemMONITOR \
  --duration 20
```

串口名替换为实际设备。注入工具会先检查固件版本、空闲状态和开漏配置，再开始倒计时。
仅复位命令也提供相同的明确操作时间点，便于观察相机屏幕。
线序与换线时机见硬件说明；记录格式见 [协议](PROTOCOL.md)。
有界的 `--pulses` 模式只用于被动复位线捕获；普通复位和恢复使用默认的单脉冲。
当前固件还会返回脉冲前、脉冲中、脉冲后的 GP27 焊盘电平及 GPIO 复用功能。
期望为 `before=1`、`during=0`、`after=1`、`gpio_function=5` (SIO)。
主机工具仍兼容旧固件的空回复。
`--pulse-us` 可请求 10 us 至 100 ms 的诊断脉宽；注入流程不设置它，
继续使用正常的 10 us 复位。
当固件返回 GP27 观测值时，注入工具也会显示并记录它。

`monitor_line.py` 把空闲的第二块 Pico 当作被动 GP28 跳变监视器。
只将监视 Pico 的 GP28 接到待测的相机侧信号，GND 接公共地；
不接它的 5V 和 GP27。工具会拒绝非空闲或启用上下拉的 Pico，
只报告跳变数和边沿时间；不驱动 GP28、不发复位脉冲、不保存原始波形。
第一块 Pico 注入时，在第二块 Pico 上运行该工具。

# Stage1 — USB transport / 第一级：USB 传输

Loaded into SRAM by Pico through the BootROM serial path. Provides USB
communication, bounded memory reads and the load/call interface used by stage2.
It stays resident while stage2 runs; its function addresses form the pinned ABI.

通过 Pico 经 BootROM 串口注入 SRAM，提供 USB 通信、内存读取和 stage2 加载接口。
stage2 运行时 stage1 仍常驻，其函数地址是两级配对的 ABI。注入上限为 8168 B。

Published image / 正式镜像：`../prebuilt/stage1.bin`。
From `fastboot/`, run `make build` to build the complete pair.
The current source candidate holds the camera LED solid while waiting for the
breakout-to-PC cable handoff and turns it off only after VBUS goes low then
high. This change is not part of the published image until hardware validation
and paired-ABI review are complete.

当前源码候选版在等待从转接板换到电脑 USB 线时会让相机 LED 常亮；
只有检测到 VBUS 先低后高才熄灭。完成实机验证和配对 ABI 审查前，
此改动不进入正式镜像。
See [usage](../README.md), [中文说明](../README.zh-CN.md) and
[development](../../CONTRIBUTING.md).

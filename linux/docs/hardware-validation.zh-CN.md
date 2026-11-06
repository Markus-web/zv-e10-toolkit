# Linux 主机实机验证：固件 30110_05

[English](hardware-validation.md)

本记录汇总一台自有 Sony ZV-E10（固件 `30110_05.2025031501`）上的只读 Linux 主机会话。原始证据和相机数据不进入仓库。

## 连接与边界

- 主机：Linux x86_64。
- 物理连接：一根直连 USB-C 数据线。
- 初始 USB 状态：Sony 海量存储（`054c:0d95`）。
- 路线：由仓库权限启动脚本打开相机 Linux 服务接口。
- 采集命令不对相机执行持久写入。服务认证可能会刷新
  `/setting/.etools` 和 `/setting/.hasp`。
- Fastboot：未在相机上尝试。直连 USB 不能替代 fastboot 路线所需的 RP2040、CC 转接板和 UART 注入。

## 结果

| 检查 | 结果 |
|---|---|
| 服务 root 终端 | 正常打开并关闭；相机返回海量存储状态 |
| 文件清单 | 1,139 个路径；验证了 BusyBox 缺少 `find` 时的回退路径 |
| 关键文件阶段 | 清单 79 项；复制并独立复算哈希 78 项 |
| 跳过的大文件 | `/setting/psd.bin` 超过单文件 4 MiB 上限；其内容仍由原始 eMMC 备份覆盖 |
| Linux 可见原始 eMMC | 完成接收时与主机磁盘重读校验；摘要随私有证据保存 |
| BootROM 范围 | 两次读取 `0xffff0000–0xffff5fff`（24 KiB），内容一致 |
| BootROM SHA-256 | `c068b4e9222970263b376c1298fa5714670b205d183dd8fa77413a2b43d17939` |
| 运行时快照 | 完成 16 项固定只读采集；终端关闭并返回海量存储状态 |
| 深层硬件快照 | 完成 111 项默认只读采集；终端关闭并返回海量存储状态 |
| CPU 拓扑 | 实机启用四个 ARMv7 Cortex-A5 核心 |
| GPE 中断 | IRQ 76（`dmpgles2`）活动，可作为 QEMU 硬件模型参考 |
| 运行时 UART | `uart0` 的 `ttyAM0` 和 `uart3` 的 `ttyAM1` 使用 AMBA PL011 兼容 ID `00241011` |
| Linux 输入类 | 仅有虚拟 `mice` 节点；未暴露实体触摸屏输入节点 |
| 相机输入路径 | `im.elf` 拥有 `I-TpMain`、`I-TpRecv`、`I-InputMain`、`I-InputRecv` 和多个 `I-InputEvent` 线程 |
| USB 设备控制器 | DWC3 gadget 以 high-speed 配置；控制器报告 SuperSpeed 上限，不是 OTG |
| 标准 Linux 类 | 未暴露 video4linux、sound、power-supply、thermal、GPIO、I2C-adapter 或 MMC-host 类 |
| 相机应用 | `im.elf` 有 188 个线程，直接持有 GPE、stream、USB gadget、USB 服务、存储和 `/dev/mem` 节点 |
| 专有硬件图 | UDM 暴露定时器、18 组 GPIO、XDMAC、MMC/eMMC、I2C、SPI、HDMI/CEC、USB 和 DMA330 的 MMIO/IRQ 拓扑 |
| 输入调度 | 触摸和输入工作线程使用专有 OSAL、futex 与 `utimer_res_sleep` 等待路径，而非 Linux input 事件 |
| USB 调度 | USB 工作线程使用 `usb_event_read`、poll、OSAL 与 futex 等待路径 |
| 启动状态 | UPM 报告 `NORM`；快照期间为 optimize/normal 状态，且无 swap 文件 |
| eMMC 健康 | Alfred 报告正常的预寿命终止与寿命值，且无读写重试计数 |
| 隐藏调整审计 | 录像限制已为 `13h 01m`，PAL/NTSC 选择器和 USB app-installer 标志已启用；旧版 4K 限制属性不存在；已启用 18/35 种语言；未写入设置 |
| 临时助手 | 从 `/tmp_network` 执行，完成后删除 |
| Linux 离线测试 | 25 项通过 |
| Fastboot 离线测试 | 18 项通过；ABI 与正式配对检查通过 |

BootROM 助手首次选择了此固件不存在的 tmpfs 路径，并在未改变相机的情况下停止。维护后的启动器只从明确白名单（`/tmp_bt`、`/tmp_network`、`/tmp_ipsec`）选择，并拒绝其他位置。

## 本记录证明的范围

在上述固件和主机上，Linux 路线可通过直连 USB 完成清单、选定文件备份、Linux 可见原始 eMMC 备份、离线校验以及文档规定的 24 KiB BootROM 读取。它不证明 fastboot 进入、分区恢复、隐藏存储、RPMB 访问，也不覆盖无法启动 Linux 的相机。

运行时和深层硬件快照在不执行持久写入命令的前提下建立了模拟器参考基线。
四个 CPU 核心均在线，GPE 完成使用 IRQ 76，两个 SoC UART 都识别为 PL011 兼容
AMBA 设备。DWC3 是通过常规 sysfs 暴露的唯一活动 platform 外设，当前以 high-speed
gadget 运行，但报告 SuperSpeed 上限。PCI 以及标准 Linux 媒体、输入、声音、传感器和
电源类均未暴露相机硬件。

专有 UDM 清单补足了模拟器所需的硬件图：四个硬件定时器、18 组 GPIO、XDMAC、
三个 MMC 控制器、eMMC、两组 I2C 和两组 SPI 控制器、HDMI/CEC、USB 与 DMA330，
并带有对应物理地址范围和 IRQ。活动 USB 控制器报告原生高速能力，但当前 gadget
配置与主机描述符仍是 USB 2 high-speed。UPM 报告正常启动；固件字符串和 init
解析器表明 `usbj` 是 USB 充电模式，不是进入 BootROM USB 或 fastboot 的软件路径。

相机应用改为通过专有设备节点和直接物理内存映射控制硬件。实时线程名将触摸定位于
`I-TpMain`/`I-TpRecv`，将输入送入 `I-InputMain`/`I-InputRecv`，再分发给多个
`I-InputEvent` 工作线程。它们通过 Sony OSAL、futex 和微定时器路径等待；USB
工作线程也通过 Sony USB 事件驱动等待。这与模拟器中触摸不经由常规 Linux
输入设备的发现一致。维护的深层工具完成全部 111 项默认采集，关闭终端并使相机
返回海量存储状态。其私有清单的 SHA-256 为
`15705a4ee9cea760b7e065b856678cb66c2d6b5d3ea54c656b899fbcebc1e3e8`。

其余 34 个厂商诊断文件以独立的 `--only` 目标维护，并已按小组逐一实测。它们提供
寄存器快照、驱动帮助、启动状态、输入表和存储健康信息，但没有发现额外的 USB
启动切换。一次广泛探索会话因某个厂商 procfs 读取拖慢 shell 而中止，因此这些读取
不属于默认采集。

传输、权限启动、临时助手位置、设备路径、备份语义或测试固件发生变化后，应重新进行实机验证。

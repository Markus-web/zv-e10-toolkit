# 应用于 ZV-E10 的跨机型研究

[English](cross-camera-research.md)

Sony 其他相机的研究可以提供假设和文件格式，但不能直接提供可复用的地址。本次比较使用
[`RafalB82/sony-a6000-re`](https://github.com/RafalB82/sony-a6000-re) 的
`e73517998e92a186e247da32cf84ea305fd206a1` 版本，以及
[`nicolvus/a6000-fw-decomp`](https://github.com/nicolvus/a6000-fw-decomp) 的
`d07ae93f15b790ff17746d79537ac1a886c2796e` 版本。

## 已确认可复用的发现

| A6000 发现 | ZV-E10 结果 | 用途 |
|---|---|---|
| Sony `Backup.bin` BK 格式和 Sony-PMCA-RE 解析器 | 私有 ZV-E10 文件可解析为校验和有效的 BK4，包含 819 个子系统和 33,178 个属性 | 离线结构和后续差异分析 |
| Musashi、SABIN 和 scenario 层 | ZV-E10 包含 Musashi 命名的 SABIN 程序、`scenario.elf` 和对应的 scenario 插件系列 | 命名与子系统映射 |
| DFE/Regulus/ZPD 划分 | ZV-E10 的 `av-cam.bin` 包含 Regulus、ZPD、DFE camera 和 SSG 路径，并另有 `dfe_app.bin` 与 `dfe_dat.bin` | 传感器前端分析目标 |
| TPZL/LDEC 压缩映像 | ZV-E10 启动映像、内核模块和 snapshot-boot 程序中存在 TPZL 标记 | 后续重建映像前加入硬件几何限制检查 |
| 更新器标志文件 | ZV-E10 库和脚本引用 `/setting` 下的 `updater/mode`、`mode1`、`mode2`、`mode3`、`mode5` 和 `mode6` | 静态启动路径线索；没有恢复方案时不得在实机创建这些文件 |
| USB 充电模式不是恢复 USB | ZV-E10 的 `usbj` 明确表示 USB 充电模式；未发现 BootROM 或 fastboot 切换 | 排除普通线缆通过充电模式进入恢复的假设 |

经过脱敏的离线检查器用法如下：

```sh
./scripts/inspect_backup.sh /private/path/Backup.bin
./scripts/inspect_backup.sh --json /private/path/Backup.bin
```

它会有意省略区域、型号、序列号、属性 ID 和属性值。A6000 研究工具默认输出其中部分
字段，未经筛选不得用于公开日志。

## 不能直接迁移的发现

- A6000 Loader3 地址、SWD 焊盘、bootloader 检查和内存图属于 CXD90014 固件与
  A6000 主板，不能作为 ZV-E10 地址。
- A6000 DFE 命名脚本针对一个加载到 `0x01000000` 的 64 KiB 原始映像。ZV-E10
  对 DFE 内容采用不同拆分，名称与偏移必须重新分析。
- A6000 TPZL 限制可用作重要验证清单，但不能证明后续每个 loader 使用完全相同的限制。
- ZV-E10 的 `MPR_SCN_GET_TOTAL_LOG.so` 插件会打开 `/log/mprlog.bin` 和
  `/dev/mem`；只读实机会话未运行该插件。
- 创建更新器 mode 文件属于持久写入，可能改变下一次启动。仅有静态证据不能证明它是
  安全的 fastboot 路线。

## 后续所需证据

1. 在考虑 SWD 前，先从 ZV-E10 自身的维修手册或连续性测量确认其 SoC 与调试焊盘。
2. 映射 ZV-E10 loader 对 `/setting/updater/mode*` 的读取，并在不创建标志文件的
   前提下确定各模式的 USB 身份。
3. 在复用任何 A6000 编码器或补丁流程前，使用未修改的 Sony 映像验证 ZV-E10 的
   TPZL 数据块几何限制。
4. 将 `dfe_app.bin`、`dfe_dat.bin` 及其加载路径作为 ZV-E10 专用二进制分析；仅在
   字符串或控制流吻合时使用 A6000 Regulus 名称。

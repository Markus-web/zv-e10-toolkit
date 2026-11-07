[English](hardware.md) | **简体中文**

# 硬件与接线

## 物料清单

已验证的方案使用下列部件。制造商料号比经销商库存号更重要。

| 数量 | 用途 | 选定部件 |
|---:|---|---|
| 1 | RP2040 发送器 | Raspberry Pi Pico H `SC0917`（已焊排针） |
| 1 | 相机插头转接板 | Saiko `BRK-USB-CPV3.0`，全引脚 USB-C 公头转接板 |
| 1 | 必需的复位保护 | Yageo `CFR-25JB-52-470R`，470Ω，1/4 W |
| 1 | 可选的串口保护 | 同款 470Ω 电阻；见下方接线图 |
| 1 | CC 共用下拉 | Yageo `CFR-25JB-52-5K1`，5.1kΩ，1/4 W |
| 1 | Pico 编程线 | USB-A 转 Micro-B **数据**线 |
| 按需 | 连接材料 | 短的 22-28 AWG 绝缘线和热缩管 |

DigiKey Finland 当前产品页：[Pico H](https://www.digikey.fi/en/products/detail/raspberry-pi/SC0917/16608257)、
[Saiko 转接板](https://www.digikey.fi/en/products/detail/saiko-systems-ltd/BRK-USB-CPV3-0/15283090)、
[470Ω 电阻](https://www.digikey.fi/en/products/detail/yageo/CFR-25JB-52-470R/2211)、
[5.1kΩ 电阻](https://www.digikey.fi/en/products/detail/yageo/CFR-25JB-52-5K1/2236)和
[短 Micro-B 数据线](https://www.digikey.fi/en/products/detail/cvilux-usa/DH-20M50057/13177527)。
电阻可多买几个备用。第二块转接板可防止手工装配时损坏后需要重新下单，但电路只需要一块。

细尖直头 ESD 安全镊子便于固定导线和电阻引脚。低成本选择为
[Seeed/Vetus 12 型镊子 `404070001`](https://www.digikey.fi/en/products/detail/seeed-technology-co-ltd/404070001/5488233)。
镊子不能替代细头烙铁、助焊剂、绝缘、应力消除和导通测试。

## 接线图

```
相机 USB-C 母座
      ↑ 插上
USB-C 公头（24pin 小板，A/B 两面都引出）
      │
      ├─ A7  D− ──[可选 470Ω]── GP28   Pico 串口 TX（open-drain）
      ├─ A6  D+ ── 470Ω ────── GP27   复位
      ├─ A5  CC1 ─┐
      ├─ B5  CC2 ─┴─ 5.1kΩ ── GND
      ├─ VBUS（A4/A9/B4/B9 任一根）── Pico 5V
      └─ GND（A1/A12/B1/B12 任一根）── Pico GND
```

备注：**A6/A7 不行的话，尝试 B6/B7。**

## 说明

- 相机侧是 USB-C 母座，必须用公头 24pin 小板才能接触引脚；
- 注入期间相机 USB-C 接 24pin 小板，不接电脑；
- D− 使用 open-drain，不要 3.3V 推挽；
- GP28 和 GP27 不能互换；
- GP29（MULTI_RX）当前不接；
- 470Ω：GP27 → D+ 必需；GP28 → D− 可选；
- 先把 CC1 和 CC2 并接，再从这个共用节点通过**一个** 5.1kΩ 电阻接地。不要把接线图理解为每个 CC 引脚各用一个电阻；
- VBUS、GND 各接一根即可，相机内部已经并联。

## 装配验收

Saiko 板只是裸转接板，不是成品恢复线。如果交给电子维修店或创客装配，
请提供本页并要求：

1. 使用短绝缘线，所有焊点绝缘，并加机械应力消除，避免裸板撬动相机插座；
2. 放大检查所有焊点；
3. 按接线图逐点测量导通，包括共用 CC 节点以及分开的 GP27/GP28 路径；
4. 连接相机前，检查 VBUS、GND、D+、D−、CC 及相邻焊盘之间没有短路；
5. Pico 3.3 V 不得连接到相机信号脚，也不得用只有 4 或 6 引脚的简化 USB-C 转接板替代。

不要用相机测试未完成的接线。应先完成并记录无源导通检查。

## 电池与复位

- 电池插着，相机正常开机；
- 脚本先开载波，再发 GP27 10 µs 低脉冲复位相机，然后整组重放；
- **有复位后不需要拔电池**；拔电池冷启动是旧的 v7 方法，当前不用。

## 换线到电脑

- payload 检测 VBUS 低 → 高；看到长闪后把 24pin 小板从相机拔下，换普通 USB-C 线接到电脑；
- Pico 5V 和 Mac 5V 会在相机 VBUS 上顶在一起，Pico 可能从 Mac 掉线，不影响已经在运行的 payload。

## LED

- 一次长闪（0.4 s）：payload 活着；
- 短脉冲计数：USB 时钟/PHY → DWC3 → EP0 配置 → 等主机；
- 之后每 2 秒一次短脉冲：在等主机枚举；
- 停在第 N 个短脉冲：对应步骤没有返回。

## 停止 / 恢复正常启动

从仓库根目录：

```sh
python3 fastboot/pico/reset_only.py --port /dev/cu.usbmodemXXXX
```

发一次 GP27 复位、关闭载波，相机回到正常启动，不用拆电池。也可以直接断电/取电池：
payload 在 SRAM，易失。

## 边界

- 这是 BootROM 串口启动，不是运行时漏洞；需要专用接线和复位时序。
- 只写 SRAM；不写 eMMC、SD 或 OTP。

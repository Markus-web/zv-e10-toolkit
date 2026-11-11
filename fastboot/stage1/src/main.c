#include "io.h"
#include "led.h"
#include "log.h"
#include "timer.h"
#include "usb_phy.h"
#include "dwc3.h"
#include "usb.h"

/*
 * ZV-E10 (CXD90045) fastboot payload -- USB transport only.
 *
 * Breadcrumbs (each is N quick flashes, then a short gap):
 *   1  USB clock/PHY init done
 *   2  DWC3 core init done
 *   3  DEPSTARTCFG done
 *   4  EP0 OUT configured
 *   5  EP0 IN configured
 *   6  EP0 enabled and SETUP armed
 *   7  D+ pull-up asserted (dwc3_connect)
 *   then one short pulse every 2 s while waiting for the host.
 *
 * A stop after N flashes means the next call never returned. The previous
 * build blinked a single 1L2S and then went silent, which could not tell a
 * hang in ep0 setup from a payload that was simply waiting.
 */

/*
 * Wait for the cable to move from the serial-boot bridge to the PC before
 * touching the DWC3.
 *
 * With the bridge still attached, the injector keeps toggling D- while the
 * USB PHY is live, and the host connection cannot happen anyway. VBUS goes
 * low when the bridge is unplugged and high again when the PC is plugged in
 * (OTG_USB_ID_EXT bit 0). Keep the front LED solid throughout this handoff:
 * solid means "insert the normal USB-C cable now". Do not time out and start
 * DWC3 without an observed low-to-high edge; that would make the indicator
 * lie and could bring up the USB controller while the bridge is still wired.
 */
static void wait_for_handoff(void)
{
    int seen_low = 0;

    led_on();
    for (;;) {
        int vbus = usb_phy_vbus();

        if (!vbus)
            seen_low = 1;
        if (seen_low && vbus) {
            led_off();
            return;
        }
        mdelay(100);
    }
}




int main(void)
{
    int ret;

    led_init();
    timer_init();
    led_blip();

    usb_phy_init();
    led_step(1);

    wait_for_handoff();

    ret = dwc3_core_init();
    if (ret != DWC3_OK) {
        led_fail(0x2006u);
    }
    led_step(2);

    ret = usb_gadget_init();
    if (ret != 0) {
        led_fail(0x2005u);
    }

    usb_led_trace = 0;   /* reset-time ep0 re-init must not block */

    ret = dwc3_connect();
    if (ret != DWC3_OK) {
        led_fail(0x2004u);
    }
    led_heartbeat();   /* one short pulse; long patterns here would delay enumeration */

    usb_gadget_run();

    return 0;
}

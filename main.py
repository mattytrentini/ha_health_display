"""Device entry point for the Seeed Studio XIAO ESP32-C6 RGB matrix."""

import asyncio
import network

from config import (
    HOME_ASSISTANT_URL,
    HOME_ASSISTANT_TOKEN,
    PAIN_ENTITY_ID,
    WIFI_PASSWORD,
    WIFI_SSID,
)
from machine import Pin
from neopixel import NeoPixel
from pain_display import HomeAssistantClient, run_pain_display
from pixel_framebuf import HORIZONTAL, PixelFramebuffer

# Logical coordinates start at the top-left.  The reverse flags account for
# this particular panel's physical wiring while retaining that natural origin.
neo = NeoPixel(Pin(0, Pin.OUT), 60)
framebuffer = PixelFramebuffer(
    neo, 6, 10, HORIZONTAL, alternating=False, reverse_x=True, reverse_y=True
)
client = HomeAssistantClient(
    HOME_ASSISTANT_URL,
    HOME_ASSISTANT_TOKEN,
    PAIN_ENTITY_ID,
)


async def connect_wifi(timeout_seconds=30):
    """Connect the station interface, yielding while DHCP/association runs."""
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print("Connecting to Wi-Fi...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(timeout_seconds):
            if wlan.isconnected():
                break
            await asyncio.sleep(1)

    if not wlan.isconnected():
        raise RuntimeError("Wi-Fi connection timed out")
    print("Wi-Fi connected:", wlan.ifconfig()[0])


async def main():
    await connect_wifi()
    await run_pain_display(client, framebuffer, interval_seconds=10)


asyncio.run(main())

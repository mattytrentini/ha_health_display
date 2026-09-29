"""Poll a Home Assistant numeric entity and render it on a 2 x 10 LED bar.

The networking request is deliberately synchronous: ``urequests`` is the
smallest and most widely available HTTP client in MicroPython.  The scheduler
is asynchronous, so the display can later share the event loop with Wi-Fi
maintenance, animations, or other tasks.
"""

import asyncio


BAR_WIDTH = 2
BAR_HEIGHT = 10
BAR_PIXELS = BAR_WIDTH * BAR_HEIGHT
# At most ~8% channel intensity: intentionally gentle for a 60-pixel matrix.
GREEN = 0x00A0
YELLOW = 0x10A0
RED = 0x1000


class HomeAssistantClient:
    """Minimal client for ``GET /api/states/<entity_id>``."""

    def __init__(self, base_url, token, entity_id):
        self.url = "%s/api/states/%s" % (base_url.rstrip("/"), entity_id)
        self.headers = {
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }

    def pain_level(self):
        # Import here so importing this module on a desktop does not require
        # MicroPython's urequests package.
        import urequests

        response = None
        try:
            response = urequests.get(self.url, headers=self.headers)
            if response.status_code != 200:
                raise RuntimeError("Home Assistant returned HTTP %s" % response.status_code)
            state = response.json()["state"]
            value = float(state)
        finally:
            if response is not None:
                response.close()

        if value < 0 or value > 10:
            raise ValueError("pain level must be in the range 0..10, got %r" % value)
        return value


def _clear(framebuffer):
    """Clear common framebuffer implementations without coupling to one API."""
    if hasattr(framebuffer, "fill"):
        framebuffer.fill(0)
        return
    if hasattr(framebuffer, "clear"):
        framebuffer.clear()
        return
    for y in range(BAR_HEIGHT):
        for x in range(BAR_WIDTH):
            _set_pixel(framebuffer, x, y, 0)


def _set_pixel(framebuffer, x, y, colour):
    if hasattr(framebuffer, "set_pixel"):
        framebuffer.set_pixel(x, y, colour)
    elif hasattr(framebuffer, "pixel"):
        framebuffer.pixel(x, y, colour)
    else:
        raise TypeError("framebuffer needs set_pixel(x, y, colour) or pixel(x, y, colour)")


def _show(framebuffer):
    if hasattr(framebuffer, "show"):
        framebuffer.show()
    elif hasattr(framebuffer, "write"):
        framebuffer.write()
    else:
        raise TypeError("framebuffer needs show() or write()")


def colour_for_pain_level(pain_level):
    """Return a dim green-to-yellow-to-red RGB565 gradient for 0--10."""
    if pain_level < 0 or pain_level > 10:
        raise ValueError("pain level must be in the range 0..10")
    if pain_level <= 5:
        return _interpolate_rgb565(GREEN, YELLOW, pain_level / 5)
    return _interpolate_rgb565(YELLOW, RED, (pain_level - 5) / 5)


def _interpolate_rgb565(start, end, amount):
    """Linearly interpolate two RGB565 colours without using float-heavy APIs."""
    start_red, start_green, start_blue = (start >> 11) & 0x1F, (start >> 5) & 0x3F, start & 0x1F
    end_red, end_green, end_blue = (end >> 11) & 0x1F, (end >> 5) & 0x3F, end & 0x1F
    red = int(start_red + (end_red - start_red) * amount + 0.5)
    green = int(start_green + (end_green - start_green) * amount + 0.5)
    blue = int(start_blue + (end_blue - start_blue) * amount + 0.5)
    return (red << 11) | (green << 5) | blue


def render_pain_level(framebuffer, pain_level, colour=None):
    """Render a bottom-up, two-pixel-wide 0--10 bar and flush it.

    Each pain point lights two LEDs.  Fractional values round to the nearest
    LED pair (for example, 4.5 lights nine LEDs).  ``(0, 9)`` is the bottom
    left LED; this assumes the matrix's coordinate system starts at top left.
    """
    if pain_level < 0 or pain_level > 10:
        raise ValueError("pain level must be in the range 0..10")

    if colour is None:
        colour = colour_for_pain_level(pain_level)

    # Half-up rounding avoids the surprising banker's rounding of round().
    lit_pixels = int(pain_level * 2 + 0.5)
    _clear(framebuffer)
    for pixel_index in range(lit_pixels):
        x = pixel_index % BAR_WIDTH
        y = BAR_HEIGHT - 1 - (pixel_index // BAR_WIDTH)
        _set_pixel(framebuffer, x, y, colour)
    _show(framebuffer)


async def run_pain_display(client, framebuffer, interval_seconds=30):
    """Immediately query/render, then repeat indefinitely every interval."""
    while True:
        try:
            render_pain_level(framebuffer, client.pain_level())
        except Exception as error:
            # Keep the last successful display visible and try again later.
            print("Pain display update failed:", error)
        await asyncio.sleep(interval_seconds)

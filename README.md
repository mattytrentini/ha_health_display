# Pain display

This MicroPython application polls a Home Assistant entity every 30 seconds
and renders its numeric state (0--10) as a red two-column bar on a 6 x 10 RGB
matrix. A value of `10` lights all 20 pixels in columns `x=0` and `x=1`; the
bar fills from the bottom upward. Its whole-bar colour follows a dim gradient:
green at 0, yellow at 5, and red at 10, with a distinct interpolated colour
at every whole-number level.

## Setup

1. On the connected board, install the app and its `pixel_framebuf`
   dependency in one command:

   ```python
   import mip
   mip.install("github:mattytrentini/ha_health_display")
   ```

   Or, from the host:

   ```sh
   mpremote mip install github:mattytrentini/ha_health_display
   ```

2. Create a root-level `config.py` from `config.py.example` and set the Home Assistant URL,
   a [long-lived access token](https://www.home-assistant.io/integrations/http/#long-lived-access-tokens),
   entity ID, Wi-Fi SSID, and Wi-Fi password.
3. Start the application with `import main` at the REPL, or copy `main.py`
   from `/lib` to the filesystem root to start it automatically after reset.

The installer puts application modules in `/lib`, as is standard for `mip`.
`config.py` deliberately remains separate because it contains credentials and
is excluded from Git.

`main.py` is configured for the supplied wiring: GPIO 0, a 6 x 10 matrix,
horizontal non-serpentine addressing, and both logical axes reversed. The
`PixelFramebuffer` library provides the expected drawing API. The renderer
also accepts the equivalent common method names if you later replace it:

| Operation | Supported methods |
| --- | --- |
| Clear pixels | `fill(0)` or `clear()` |
| Set an LED | `set_pixel(x, y, colour)` or `pixel(x, y, colour)` |
| Send pixels | `show()` or `write()` |

## Home Assistant request

It requests `GET /api/states/<entity_id>` with a Bearer token and reads the
`state` field. The entity must currently be a numeric value from 0 to 10.
At startup, the application connects to Wi-Fi and waits up to 30 seconds for
an IP address. Network/API errors leave the last displayed value intact and
are retried at the next interval.

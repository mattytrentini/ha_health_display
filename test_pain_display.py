import unittest

from pain_display import GREEN, RED, YELLOW, colour_for_pain_level, render_pain_level


class FakeFramebuffer:
    def __init__(self):
        self.pixels = {}
        self.shown = False

    def fill(self, colour):
        self.pixels = {(x, y): colour for x in range(6) for y in range(10)}

    def set_pixel(self, x, y, colour):
        self.pixels[(x, y)] = colour

    def show(self):
        self.shown = True


class RenderPainLevelTests(unittest.TestCase):
    def test_zero_lights_no_pixels(self):
        framebuffer = FakeFramebuffer()
        render_pain_level(framebuffer, 0)
        self.assertEqual(sum(c != 0 for c in framebuffer.pixels.values()), 0)
        self.assertTrue(framebuffer.shown)

    def test_ten_lights_all_twenty_bar_pixels(self):
        framebuffer = FakeFramebuffer()
        render_pain_level(framebuffer, 10)
        lit = [point for point, colour in framebuffer.pixels.items() if colour == RED]
        self.assertEqual(len(lit), 20)
        self.assertEqual(set(lit), {(x, y) for x in range(2) for y in range(10)})

    def test_midpoint_fills_bottom_five_rows(self):
        framebuffer = FakeFramebuffer()
        render_pain_level(framebuffer, 5)
        lit = [point for point, colour in framebuffer.pixels.items() if colour == YELLOW]
        self.assertEqual(set(lit), {(x, y) for x in range(2) for y in range(5, 10)})

    def test_colour_gradient_endpoints(self):
        self.assertEqual(colour_for_pain_level(0), GREEN)
        self.assertEqual(colour_for_pain_level(5), YELLOW)
        self.assertEqual(colour_for_pain_level(10), RED)


if __name__ == "__main__":
    unittest.main()

"""Tests for the procedural VANES brand icon and its bundled assets."""

import os
import tempfile
import unittest

from PIL import Image

from vanes.branding import (
    ICON_SIZES,
    asset_path,
    render_icon,
    write_ico,
    write_png,
)


class BrandingTests(unittest.TestCase):
    """Validate the square app icon renders and the bundled assets are usable."""

    def test_render_icon_is_square_rgba(self):
        for size in (16, 64, 256):
            img = render_icon(size)
            self.assertEqual(img.size, (size, size))
            self.assertEqual(img.mode, "RGBA")

    def test_asset_path_resolves_inside_assets_dir(self):
        path = asset_path("vanes_icon.ico")
        self.assertTrue(path.endswith(os.path.join("assets", "vanes_icon.ico")))

    def test_bundled_ico_exists_and_is_multi_resolution(self):
        ico = asset_path("vanes_icon.ico")
        self.assertTrue(os.path.exists(ico), "committed .ico is missing")
        with Image.open(ico) as img:
            self.assertEqual(img.format, "ICO")
            self.assertEqual(sorted(img.info.get("sizes", set())), sorted(ICON_SIZES))

    def test_bundled_png_exists_and_is_square(self):
        png = asset_path("vanes_icon.png")
        self.assertTrue(os.path.exists(png), "committed .png is missing")
        with Image.open(png) as img:
            self.assertEqual(img.format, "PNG")
            self.assertEqual(img.size, (256, 256))

    def test_write_ico_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "out.ico")
            self.assertEqual(write_ico(target), target)
            with Image.open(target) as img:
                self.assertEqual(img.format, "ICO")
                self.assertIn((64, 64), img.info.get("sizes", set()))

    def test_write_png_round_trips(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = os.path.join(tmp, "out.png")
            self.assertEqual(write_png(target, 48), target)
            with Image.open(target) as img:
                self.assertEqual(img.format, "PNG")
                self.assertEqual(img.size, (48, 48))


if __name__ == "__main__":
    unittest.main()

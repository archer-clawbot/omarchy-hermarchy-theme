import math
import tomllib
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SHELL_THEME = ROOT / "shell.toml"
SUPPORTED_DEVICE_SCALES = (1.0, 1.25, 1.5, 2.0)


def rgb(hex_color):
    value = hex_color.removeprefix("#")
    if len(value) != 6:
        raise AssertionError(f"expected #RRGGBB, got {hex_color!r}")
    return tuple(int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))


def composite(foreground, alpha, background):
    return tuple(alpha * channel + (1 - alpha) * base for channel, base in zip(foreground, background))


def darker(color, factor):
    return tuple(channel / factor for channel in color)


def relative_luminance(color):
    def linear(channel):
        return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4

    red, green, blue = (linear(channel) for channel in color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def contrast_ratio(first, second):
    light, dark = sorted((relative_luminance(first), relative_luminance(second)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


def color_distance(first, second):
    return math.sqrt(sum((left - right) ** 2 for left, right in zip(first, second)))


def toggle_geometry(control_height, device_scale):
    # Mirrors Omarchy Ui/ToggleSwitch.qml. Integer logical dimensions avoid
    # scale-dependent collapse; physical sizes prove the thumb remains present.
    track_height = max(22, round(control_height * 0.55))
    track_width = round(track_height * 1.9)
    knob_size = max(6, round(track_height * 0.72))
    knob_inset = max(1, round((track_height - knob_size) / 2))
    off_x = knob_inset
    on_x = track_width - knob_size - knob_inset
    return {
        "track_width": track_width * device_scale,
        "track_height": track_height * device_scale,
        "knob_size": knob_size * device_scale,
        "inset": knob_inset * device_scale,
        "off_x": off_x * device_scale,
        "on_x": on_x * device_scale,
    }


class ToggleThemeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.theme = tomllib.loads(SHELL_THEME.read_text())
        cls.controls = cls.theme["controls"]
        cls.popup = rgb(cls.theme["popups"]["background"])
        cls.foreground = rgb(cls.controls["normal-color"])
        cls.active = rgb(cls.theme["bar"]["active"])
        cls.selected = rgb(cls.controls["selected-color"])
        cls.enabled_track = composite(
            cls.selected,
            cls.controls["selected-fill-alpha"],
            cls.popup,
        )
        cls.disabled_track = composite(
            cls.foreground,
            cls.controls["normal-fill-alpha"],
            cls.popup,
        )
        cls.disabled_thumb = darker(cls.foreground, 1.25)

    def test_enabled_toggle_thumb_contrasts_with_track(self):
        self.assertGreaterEqual(
            contrast_ratio(self.selected, self.enabled_track),
            3.0,
            "enabled ToggleSwitch thumb must remain visibly distinct from its selected track",
        )

    def test_enabled_state_uses_restrained_semantic_cyan(self):
        self.assertEqual(self.selected, self.active)
        self.assertEqual(rgb(self.controls["selected-border"]), self.active)
        self.assertGreaterEqual(self.controls["selected-fill-alpha"], 0.12)
        self.assertLessEqual(self.controls["selected-fill-alpha"], 0.25)

    def test_disabled_state_is_muted_and_visually_distinct(self):
        self.assertNotEqual(self.foreground, self.active)
        self.assertLessEqual(self.controls["normal-fill-alpha"], 0.08)
        self.assertGreaterEqual(contrast_ratio(self.disabled_thumb, self.disabled_track), 3.0)
        self.assertGreater(color_distance(self.enabled_track, self.disabled_track), 0.08)
        self.assertGreater(color_distance(self.selected, self.disabled_thumb), 0.25)

    def test_active_threshold_checked_path_cannot_use_off_palette(self):
        # The battery caller maps active thresholds to checked=true. The stock
        # switch then consumes selected-*; this guards that path from silently
        # regressing to the normal/off palette again.
        self.assertNotEqual(self.controls["selected-color"], self.controls["normal-color"])
        self.assertNotEqual(self.controls["selected-fill-alpha"], self.controls["normal-fill-alpha"])
        self.assertNotEqual(self.enabled_track, self.disabled_track)

    def test_thumb_geometry_survives_normal_and_high_dpi_scaling(self):
        for device_scale in SUPPORTED_DEVICE_SCALES:
            with self.subTest(device_scale=device_scale):
                geometry = toggle_geometry(control_height=40, device_scale=device_scale)
                self.assertGreaterEqual(geometry["knob_size"], 6 * device_scale)
                self.assertGreaterEqual(geometry["inset"], device_scale)
                self.assertGreaterEqual(geometry["off_x"], geometry["inset"])
                self.assertGreaterEqual(geometry["on_x"], geometry["off_x"])
                self.assertLessEqual(
                    geometry["on_x"] + geometry["knob_size"] + geometry["inset"],
                    geometry["track_width"],
                )
                self.assertLessEqual(
                    geometry["knob_size"] + geometry["inset"] * 2,
                    geometry["track_height"],
                )


if __name__ == "__main__":
    unittest.main()

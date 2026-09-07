"""Functional regressions: actual Qt mouse events, image edits and file I/O."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import tempfile
import unittest
from unittest.mock import patch
from PIL import Image, ImageChops
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication, QDialog
from alanpaint.ui import MainWindow, DimensionsDialog
from alanpaint.commands import ReplaceImageCommand
from alanpaint.filters import apply_filter, FILTER_DEFINITIONS
from alanpaint.io import load_image, save_image, pil_to_qimage, qimage_to_pil


APP = QApplication.instance() or QApplication([])
APP.setStyle("Fusion")
for font in ("segoeui.ttf", "segoeuib.ttf"):
    path = os.path.join(os.environ.get("WINDIR", "C:/Windows"), "Fonts", font)
    if os.path.exists(path):
        QFontDatabase.addApplicationFont(path)


class EditorTests(unittest.TestCase):
    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        APP.processEvents()
        self.canvas = self.window._canvas
        self.window._load_document(Image.new("RGB", (400, 300), "#518ab7"))
        self.canvas.zoom_100()
        APP.processEvents()

    def tearDown(self):
        self.window._preview_timer.stop()
        self.window._thumbnail_timer.stop()
        self.window.hide()
        self.window.deleteLater()
        APP.processEvents()

    def point(self, x, y):
        return QPoint(*self.canvas.image_to_display(x, y))

    def stroke(self, tool="brush", start=(20, 30), end=(280, 190)):
        self.window._select_tool(tool)
        QTest.mousePress(self.canvas, Qt.LeftButton, pos=self.point(*start))
        QTest.mouseMove(self.canvas, self.point(*end))
        QTest.mouseRelease(self.canvas, Qt.LeftButton, pos=self.point(*end))

    def assertImage(self, actual, expected):
        self.assertEqual(actual.size, expected.size)
        self.assertEqual(actual.mode, expected.mode)
        self.assertEqual(actual.tobytes(), expected.tobytes())

    def test_long_brush_and_complete_history(self):
        original = self.canvas.get_image().copy()
        self.stroke()
        painted = self.canvas.get_image().copy()
        self.assertNotEqual(painted.getpixel((150, 110)), original.getpixel((150, 110)))
        self.assertEqual(painted.getpixel((10, 10)), original.getpixel((10, 10)))
        self.assertTrue(self.window._modified)
        self.window._undo()
        self.assertImage(self.canvas.get_image(), original)
        self.assertFalse(self.window._modified)
        self.window._redo()
        self.assertImage(self.canvas.get_image(), painted)

    def test_click_makes_dot_and_right_click_does_not_draw(self):
        before = self.canvas.get_image().copy()
        self.window._select_tool("brush")
        QTest.mouseClick(self.canvas, Qt.RightButton, pos=self.point(50, 50))
        self.assertImage(self.canvas.get_image(), before)
        QTest.mouseClick(self.canvas, Qt.LeftButton, pos=self.point(50, 50))
        self.assertEqual(self.canvas.get_image().getpixel((50, 50)), self.window._tool_color)

    def test_reverse_shapes_preserve_background(self):
        for tool in ("line", "rectangle", "ellipse"):
            with self.subTest(tool=tool):
                original = self.canvas.get_image().copy()
                self.stroke(tool, (250, 190), (50, 40))
                self.assertNotEqual(self.canvas.get_image().tobytes(), original.tobytes())
                self.assertEqual(self.canvas.get_image().getpixel((48, 38)), original.getpixel((48, 38)))
                self.window._undo()
                self.assertImage(self.canvas.get_image(), original)

    def test_brush_at_edge_clips_without_shifting(self):
        self.window._set_color((255, 0, 0))
        self.stroke(start=(0, 0), end=(80, 0))
        self.assertEqual(self.canvas.get_image().getpixel((40, 0)), (255, 0, 0))
        self.assertEqual(self.canvas.get_image().getpixel((40, 10)), (81, 138, 183))

    def test_outside_image_does_not_draw_edge(self):
        original = self.canvas.get_image().copy()
        QTest.mouseClick(self.canvas, Qt.LeftButton, pos=QPoint(2, 2))
        self.assertImage(self.canvas.get_image(), original)

    def test_eraser_and_undo(self):
        self.stroke("eraser", (20, 20), (200, 20))
        self.assertEqual(self.canvas.get_image().getpixel((100, 20)), (255, 255, 255))
        self.window._undo()
        self.assertEqual(self.canvas.get_image().getpixel((100, 20)), (81, 138, 183))

    def test_crop_mixed_history_restores_dimensions_and_pixels(self):
        original = self.canvas.get_image().copy()
        self.stroke()
        painted = self.canvas.get_image().copy()
        self.stroke("crop", (40, 30), (240, 180))
        QTest.keyClick(self.canvas, Qt.Key_Return)
        self.assertImage(self.canvas.get_image(), painted.crop((40, 30, 240, 180)))
        self.window._choose_filter("Invertir")
        self.window._apply_effects()
        final = self.canvas.get_image().copy()
        for _ in range(3):
            self.window._undo()
        self.assertImage(self.canvas.get_image(), original)
        for _ in range(3):
            self.window._redo()
        self.assertImage(self.canvas.get_image(), final)

    def test_crop_ratio_reverse_drag_and_cancel(self):
        original = self.canvas.get_image().copy()
        self.canvas.set_crop_ratio(1)
        self.stroke("crop", (300, 250), (50, 50))
        self.assertEqual(self.canvas.crop_rect, (100, 50, 300, 250))
        QTest.keyClick(self.canvas, Qt.Key_Escape)
        self.assertIsNone(self.canvas.crop_rect)
        self.assertImage(self.canvas.get_image(), original)
        self.assertFalse(self.window._modified)

    def test_crop_to_full_bounds(self):
        self.stroke("crop", (0, 0), (400, 300))
        self.assertEqual(self.canvas.crop_rect, (0, 0, 400, 300))

    def test_zoom_affects_geometry_and_coordinates(self):
        self.canvas.set_zoom(2)
        self.assertEqual(self.canvas.image_rect().width(), 800)
        self.assertEqual(self.canvas.display_to_image(*self.canvas.image_to_display(50, 60)), (50, 60))
        self.canvas.set_zoom(.5)
        self.assertEqual(self.canvas.image_rect().width(), 200)
        self.stroke(start=(30, 30), end=(150, 30))
        self.assertEqual(self.canvas.get_image().getpixel((100, 30)), self.window._tool_color)

    def test_space_requires_drag_for_panning(self):
        self.window._select_tool("brush")
        offset = self.canvas._offset
        QTest.keyPress(self.canvas, Qt.Key_Space)
        QTest.mouseMove(self.canvas, QPoint(30, 30))
        self.assertEqual(self.canvas._offset, offset)
        QTest.mousePress(self.canvas, Qt.LeftButton, pos=QPoint(30, 30))
        QTest.mouseMove(self.canvas, QPoint(70, 50))
        QTest.mouseRelease(self.canvas, Qt.LeftButton, pos=QPoint(70, 50))
        QTest.keyRelease(self.canvas, Qt.Key_Space)
        self.assertEqual(self.canvas._offset.x(), offset.x()+40)
        self.assertFalse(self.window._modified)

    def test_color_picker_and_hex(self):
        self.window._select_tool("picker")
        QTest.mouseClick(self.canvas, Qt.LeftButton, pos=self.point(80, 80))
        self.assertEqual(self.window._tool_color, (81, 138, 183))
        self.window._color_hex.setText("#ed6585")
        self.window._hex_changed()
        self.assertEqual(self.canvas._tool_color, (237, 101, 133))

    def test_text_insert_is_undoable_and_preserves_background(self):
        original = self.canvas.get_image().copy()
        with patch("alanpaint.ui.QInputDialog.getMultiLineText", return_value=("Hola, creación\nAlanPaint", True)):
            self.window._insert_text(50, 50)
        self.assertNotEqual(self.canvas.get_image().tobytes(), original.tobytes())
        self.assertEqual(self.canvas.get_image().getpixel((49, 49)), original.getpixel((49, 49)))
        self.window._undo()
        self.assertImage(self.canvas.get_image(), original)

    def test_filter_preview_cancel_apply(self):
        original = self.canvas.get_image().copy()
        self.window._choose_filter("Sepia")
        self.window._render_preview()
        self.assertImage(self.canvas.get_image(), original)
        self.assertFalse(self.window._modified)
        self.window._reset_effects()
        self.assertImage(self.canvas.get_image(), original)
        self.window._choose_filter("Invertir")
        self.window._adjustments["brightness"].setValue(120)
        expected = self.window._effect_result(original)
        self.window._apply_effects()
        self.assertImage(self.canvas.get_image(), expected)
        self.window._undo()
        self.assertImage(self.canvas.get_image(), original)

    def test_drawing_blocked_during_preview_debounce(self):
        original = self.canvas.get_image().copy()
        self.window._choose_filter("Sepia")
        QTest.mouseClick(self.canvas, Qt.LeftButton, pos=self.point(50, 50))
        self.assertImage(self.canvas.get_image(), original)

    def test_all_filters_preserve_alpha(self):
        image = Image.new("RGBA", (13, 7), (70, 120, 210, 84))
        for name, info in FILTER_DEFINITIONS.items():
            with self.subTest(name=name):
                args = dict(info)
                result = apply_filter(image, args.pop("name"), **args)
                self.assertEqual(result.size, image.size)
                self.assertEqual(result.getchannel("A").tobytes(), image.getchannel("A").tobytes())

    def test_auto_contrast_is_real_adjustment(self):
        image = Image.new("RGB", (100, 1))
        image.putdata([(50+x, 50+x, 50+x) for x in range(100)])
        result = apply_filter(image, "auto_contrast")
        self.assertEqual(result.getextrema()[0], (0, 255))

    def test_rotate_flip_and_resize_history(self):
        original = self.canvas.get_image().copy()
        self.window._rotate()
        self.assertEqual(self.canvas.get_image_size(), (300, 400))
        self.window._flip()
        self.window._execute(ReplaceImageCommand(self.canvas, self.canvas.get_image().resize((80, 50))))
        for _ in range(3):
            self.window._undo()
        self.assertImage(self.canvas.get_image(), original)

    def test_dimensions_keep_aspect_ratio(self):
        dialog = DimensionsDialog(self.window, (400, 300), True)
        dialog.width_box.setValue(800)
        self.assertEqual(dialog.dimensions(), (800, 600))
        dialog.height_box.setValue(150)
        self.assertEqual(dialog.dimensions(), (200, 150))

    def test_save_preview_and_revision_branch(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "image.png")
            self.window._choose_filter("Sepia")
            self.assertTrue(self.window._write_file(path))
            self.assertImage(load_image(path), self.canvas.get_image())
            self.assertFalse(self.window._modified)
            self.window._undo()
            self.assertTrue(self.window._modified)
            self.window._redo()
            self.assertFalse(self.window._modified)
            self.window._undo()
            self.stroke()
            self.assertTrue(self.window._modified)
            self.assertFalse(self.window._command_manager.can_redo())

    def test_save_as_adds_extension_once(self):
        with tempfile.TemporaryDirectory() as folder:
            for filename in ("art.png", "drawing", "photo.jpeg", "scan.tiff"):
                path = os.path.join(folder, filename)
                with patch("alanpaint.ui.QFileDialog.getSaveFileName", return_value=(path, "PNG Files (*.png)")):
                    self.assertTrue(self.window._save_image_as())
                expected = path+".png" if filename == "drawing" else path
                self.assertTrue(os.path.exists(expected))
                self.assertFalse(os.path.exists(expected+".png"))

    def test_new_action_uses_dialog_and_valid_dimensions(self):
        with patch.object(DimensionsDialog, "exec", return_value=QDialog.Accepted):
            self.window._new_action.trigger()
        self.assertEqual(self.canvas.get_image_size(), (1000, 700))

    def test_transparency_roundtrip_and_jpeg_white_background(self):
        source = Image.new("RGBA", (13, 9), (255, 0, 0, 0))
        source.putpixel((5, 5), (10, 20, 30, 200))
        self.assertImage(qimage_to_pil(pil_to_qimage(source)), source)
        with tempfile.TemporaryDirectory() as folder:
            for extension in ("png", "tiff", "webp"):
                path = os.path.join(folder, "test."+extension)
                save_image(source, path)
                reloaded = load_image(path)
                self.assertEqual(reloaded.mode, "RGBA")
                self.assertEqual(reloaded.getchannel("A").tobytes(), source.getchannel("A").tobytes())
            path = os.path.join(folder, "test.jpg")
            save_image(source, path)
            self.assertTrue(all(value > 240 for value in load_image(path).getpixel((0, 0))))


if __name__ == "__main__":
    unittest.main()

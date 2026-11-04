"""Synthetic checks for native screenshot selection and final source links."""
from __future__ import annotations

from pathlib import Path
import sys
import hashlib
from collections import defaultdict
import tempfile
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'build/tools'))
import capture_quality
import asset_gallery
import gallery_index
import compiler_portfolio


class NativeFrameTests(unittest.TestCase):
    def picture(self, rectangle=None):
        pic = Image.new('RGB', (320, 240), 'black')
        if rectangle:
            ImageDraw.Draw(pic).rectangle(rectangle, fill='white')
        return pic

    def test_boot_and_shell_are_not_program_output(self):
        boot = self.picture((60, 80, 120, 125))
        shell = self.picture((60, 60, 160, 155))
        selector = capture_quality.StableFrames(boot, shell, stable_samples=3)
        self.assertFalse(selector.observe(boot, 10000))
        self.assertFalse(selector.observe(shell, 10000))
        with self.assertRaises(RuntimeError):
            selector.result()

    def test_complete_stable_drawing_beats_transient_ink(self):
        boot = self.picture()
        partial = self.picture((50, 50, 90, 90))
        complete = self.picture((50, 50, 220, 170))
        transient = self.picture((32, 24, 285, 215))
        selector = capture_quality.StableFrames(boot, stable_samples=3)
        selector.observe(partial, 80)
        for _ in range(3):
            selector.observe(complete, 320)
        selector.observe(transient, 900)
        self.assertEqual(selector.result(require_stable=True).tobytes(), complete.tobytes())
        self.assertGreater(selector.live_score, selector.stable_score)

    def test_uniform_native_paper_is_not_program_output(self):
        boot = self.picture((60, 80, 120, 125))
        selector = capture_quality.StableFrames(boot)
        paper = Image.new('RGB', (320, 240), (0, 194, 197))
        self.assertFalse(selector.observe(paper, 10000))
        with self.assertRaisesRegex(RuntimeError, 'no distinct'):
            selector.result()

    def test_missing_static_completion_fails(self):
        selector = capture_quality.StableFrames(self.picture(), stable_samples=3)
        selector.observe(self.picture((60, 80, 90, 120)), 50)
        selector.observe(self.picture((60, 80, 120, 140)), 75)
        with self.assertRaisesRegex(RuntimeError, 'persistent'):
            selector.result(require_stable=True)

    def test_bitmaps_only_count_bitmap_ink(self):
        self.assertEqual(capture_quality.bitmap_ink(bytes(6144) + b'\xff' * 768), 0)
        self.assertEqual(capture_quality.bitmap_ink(b'\xff' * 6144 + bytes(768)), 6144 * 8)
        with self.assertRaises(ValueError):
            capture_quality.bitmap_ink(b'')


    def test_console_output_is_not_rejected_for_old_login_banner(self):
        shell = ('ZX-UX UNIX v1\nlogin: root\nWelcome to ZX-UX UNIX v1.\n'
                 '#\n1.init 2.sh\n')
        loading = (shell + '# /dev/cassette/FTH08\n'
                   'Loading: /dev/cassette/FTH08\n')
        self.assertEqual(capture_quality.program_output_lines(loading, shell), set())
        forth = loading + 'w1=hello\nw2=world\n'
        self.assertEqual(capture_quality.program_output_lines(forth, shell),
                         {'w1=hello', 'w2=world'})
        valley = loading.replace('ZX-UX UNIX v1', 'DEATH VALLEY', 1)
        self.assertIn('DEATH VALLEY',
                      capture_quality.program_output_lines(valley, shell))

    def test_documented_gameplay_protocols_for_both_emulators(self):
        from capture_replay import (steps, fuse_steps, rvm_actions,
                                    replay_requires_change)
        programs = (
            ('39-compspacegames-SpaceGames-11', ('L', '10'), ('H', 'q', .08)),
            ('50-monsters--Monsters', ('H', 'n', .14), ('H', 'f', .14)),
        )
        for name, *controls in programs:
            with self.subTest(program=name):
                recipe = steps('www.thespectrumshow.net', name)
                self.assertTrue(replay_requires_change('www.thespectrumshow.net', name))
                for action in controls:
                    self.assertIn(action, recipe)
                self.assertTrue(fuse_steps(recipe))
                self.assertTrue(rvm_actions(recipe))
        self.assertFalse(replay_requires_change('Granada-Publishing',
                                                '03-bobsleigh'))

    def test_compiler_override_applies_after_defaults(self):
        key = 'rfc:example'
        with patch.dict(compiler_portfolio.CAPTURE, {key: {'sample_step': .09,
                                                              'fuse_wait': 16,
                                                              'early_capture': False}}):
            config = compiler_portfolio.fuse_config('rfc', 'example', 'FTH01',
                                                    Path('/test.ssx'), 8)
        self.assertEqual(config['sample_step'], .09)
        self.assertEqual(config['fuse_wait'], 16)
        self.assertFalse(config['early_capture'])
        self.assertIn('reference', config)


class PortfolioScreenshotTests(unittest.TestCase):
    def test_rebuilt_captures_are_nonblank_and_not_repeated_boots(self):
        shots = ROOT / 'dist/screenshots'
        if not shots.is_dir():
            self.skipTest('full release images are built by the GitHub runner')
        for category in ('c48-bin', 'rbc-bin', 'forth-bin', 'pascal-bin', 'fortran-bin'):
            for engine in ('rvm', 'fuse'):
                folder = shots / category / engine
                self.assertTrue(folder.is_dir(), f'missing {category}/{engine}')
                duplicates = defaultdict(list)
                for image in sorted(folder.rglob('*.png')):
                    with Image.open(image) as png:
                        self.assertEqual(png.size, (576, 448) if engine == 'rvm'
                                         else (320, 240), str(image))
                        inner = png.convert('RGB').resize((128, 96))
                        # A blank image, even with a valid PNG header, is a failure.
                        colors = inner.getcolors(maxcolors=1)
                        self.assertIsNone(colors, f'blank screenshot: {image}')
                        signature = hashlib.sha256(inner.tobytes()).hexdigest()
                    duplicates[signature].append(image)
                for paths in duplicates.values():
                    self.assertLessEqual(len(paths), 2,
                        'repeated identical native screens: ' + ', '.join(str(p) for p in paths))
        self.assertFalse((shots / 'rvm').exists())
        self.assertFalse((shots / 'fuse').exists())


class ReleaseGalleryTests(unittest.TestCase):

    def test_c48_directory_identifies_original_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assets = root / 'assets'
            screenshots = root / 'screenshots'
            src = assets / 'c48-src/demos/hello.c'
            ssx = assets / 'c48-bin/ssx/hello.ssx'
            tape = assets / 'c48-bin/tzx/hello.tzx'
            for file in (src, ssx, tape):
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_bytes(file.name.encode())
            for engine in ('rvm', 'fuse'):
                png = screenshots / 'c48' / engine / 'demos/hello.png'
                png.parent.mkdir(parents=True, exist_ok=True)
                Image.new('RGB', (320, 240)).save(png)
            with (patch.object(asset_gallery, 'ASSETS', assets),
                  patch.object(asset_gallery, 'SHOTS', screenshots),
                  patch.dict(asset_gallery.SRC, {'c48-bin': ('c48-src', '.c')}, clear=True),
                  patch.dict(asset_gallery.LAYOUT, {'c48': 'c48-bin'}, clear=True),
                  patch.dict(asset_gallery.DOUBLE, {}, clear=True)):
                asset_gallery.finalize()
            for engine in ('rvm', 'fuse'):
                html = (screenshots / 'c48-bin' / engine / 'index.html').read_text()
                figure = html.split('<figure>', 1)[1].split('</figure>', 1)[0]
                self.assertIn('demos/hello.png', html)
                self.assertLess(figure.index('<img'), figure.index('<figcaption>'))
                self.assertIn('hello.c', figure)
                self.assertIn('SSX</a>', figure)
                self.assertIn('TZX</a>', figure)

    def test_multiple_originals_and_links_beneath_images(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            assets = root / 'assets'
            screenshots = root / 'screenshots'
            case = assets / 'basic-src/demo/01-sample'
            case.mkdir(parents=True)
            for name in ('First.bas', 'Second.bas', 'First.tzx', 'Second.tzx'):
                (case / name).write_text('original ' + name)
            ssx = assets / 'rbc-bin/demo/ssx/01-sample.ssx'
            tape = assets / 'rbc-bin/demo/tzx/01-sample.tzx'
            ssx.parent.mkdir(parents=True)
            tape.parent.mkdir(parents=True)
            ssx.write_bytes(b'SSX')
            tape.write_bytes(b'TZX')
            for engine in ('rvm', 'fuse'):
                pic = screenshots / 'rbc/demo' / engine / 'none.png'
                # Asset gallery expects collection underneath engine.
                pic = screenshots / 'rbc' / engine / 'demo/01-sample.png'
                pic.parent.mkdir(parents=True)
                Image.new('RGB', (320, 240)).save(pic)
            with (patch.object(asset_gallery, 'ASSETS', assets),
                  patch.object(asset_gallery, 'SHOTS', screenshots),
                  patch.dict(asset_gallery.SRC, {'rbc-bin': ('rbc-src', '.bas')}, clear=True),
                  patch.dict(asset_gallery.LAYOUT, {'rbc': 'rbc-bin'}, clear=True),
                  patch.dict(asset_gallery.DOUBLE, {}, clear=True),
                  patch.object(gallery_index, 'SCREENSHOTS', screenshots),
                  patch.object(gallery_index, 'COMPILERS', (('rbc', 'BASIC'),))):
                # Rebuild invokes the final layout function.
                gallery_index.write_index()
            for engine in ('rvm', 'fuse'):
                html = (screenshots / 'rbc-bin' / engine / 'index.html').read_text()
                self.assertEqual(html.count('<figure>'), 1)
                self.assertEqual(html.count('<figcaption>'), 1)
                figure = html.split('<figure>', 1)[1].split('</figure>', 1)[0]
                self.assertLess(figure.index('<img'), figure.index('<figcaption>'))
                for name in ('First.bas', 'Second.bas', 'First.tzx', 'Second.tzx'):
                    self.assertIn(name, figure)
                self.assertIn('SSX</a>', figure)
                self.assertIn('TZX</a>', figure)
                self.assertFalse((screenshots / engine).exists())


if __name__ == '__main__':
    unittest.main()

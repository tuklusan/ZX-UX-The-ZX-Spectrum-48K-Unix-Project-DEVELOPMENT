"""Focused tests using failures from the preserved 121-input result file."""
import importlib.util
from pathlib import Path
import unittest

MODULE = Path(__file__).resolve().parents[1] / 'stage' / 'result_classify.py'
spec = importlib.util.spec_from_file_location('result_classify', MODULE)
result_classify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(result_classify)


class ClassificationTests(unittest.TestCase):
    def test_memory_global_write(self):
        self.assertEqual(result_classify.classify('rbc: ZX-UX memory check stopped line 25: POKE global_memory_write. 6 blocked operation(s)'), 'memory-global-write')

    def test_memory_unbounded_write(self):
        self.assertEqual(result_classify.classify('rbc: ZX-UX memory check stopped line 9020: POKE unbounded_memory_write.'), 'memory-unbounded-write')

    def test_memory_global_read(self):
        self.assertEqual(result_classify.classify('rbc: ZX-UX memory check stopped line 40: PEEK global_memory_read.'), 'memory-global-read')

    def test_external_load(self):
        self.assertEqual(result_classify.classify('rbc: ZX-UX memory check stopped line 8060: LOAD tape_or_external_io.'), 'external-io')

    def test_spectrum_character(self):
        self.assertEqual(result_classify.classify("source.SourceError: no Spectrum character for '↑'"), 'character-encoding')

    def test_computed_line(self):
        self.assertEqual(result_classify.classify('Not supported line 20: computed line number'), 'computed-line')

    def test_redimension(self):
        self.assertEqual(result_classify.classify('Not supported line 2232: DIM again, with different sizes'), 'array-redimension')

    def test_val(self):
        self.assertEqual(result_classify.classify('Not supported line 160: VAL'), 'unsupported-val')

    def test_numeric_expression(self):
        self.assertEqual(result_classify.classify('Expecting a number line 4:'), 'numeric-expression')

    def test_invalid_listing(self):
        self.assertEqual(result_classify.classify('invalid BASIC text line 3'), 'source-parse')

    def test_unexpected(self):
        self.assertEqual(result_classify.classify('strange diagnostic'), 'compiler-error')


if __name__ == '__main__':
    unittest.main()
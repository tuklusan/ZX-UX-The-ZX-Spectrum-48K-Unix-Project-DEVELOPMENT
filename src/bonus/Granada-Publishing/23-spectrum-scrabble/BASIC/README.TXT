SPECTRUM SCRABBLE — Granada Publishing collection

The source program calls itself "Spectrum scramble". It is a word-search puzzle, rather than a game of placing tiles. We kept the original SpectrumScrabble.tap without changes. The supplied archive has no original TZX. We made SpectrumScrabble-derived.tzx by wrapping the original TAP records without changing their bytes. The TAP record checksums and round-trip back to the original file passed. We recovered 149 numbered BASIC lines from the resulting TZX, and a separate inspection of the original tape found the same 149 lines.

Players supply two to ten words, then search a 15 by 15 letter grid. The BASIC listing assigns 5, 8, 6 and 7 to cursor movement, W to entering a found word, and R to ending the search. We loaded the original TAP in Fuse 48K. Its saved start line runs automatically. We entered two test words, cat and dog, declined the preview, and showed the word list beside the puzzle. Then we moved the active cursor right, right, down and left. The five genuine PNG captures show the puzzle and input-driven highlight movement. We did not submit a found word or complete the puzzle. Two small words can still cause a surprising amount of paperwork for a ZX Spectrum.

REPLAY.sh uses Fuse SDL, Xvfb, the original 48K ROM, Python 3, Pillow and python-xlib. Only the original BASIC program was run. No native program was built.

Original source SHA-256:
SpectrumScrabble.tap a71f647b9f723e4b2c72ac355c6919f94f7c3dca0bba27b14fcb997d4dc2ca20
The derived TZX and text listing are not original source media.

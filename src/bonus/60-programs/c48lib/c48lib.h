/* 32x24 full-height 8x8 text and per-program glyph interface.
 * Requires frozen <c48.h> and the generated matching .asm companion.
 * 32..127 = Acer VGA printable glyphs; 128..159 = per-game glyphs.
 * Each call writes eight screen bitmap bytes and one color attribute.
 * Supports the frozen SDK's INVERSE and OVER state; no UDG slots used.
 */
int c48_cell(int row, int col, int code);

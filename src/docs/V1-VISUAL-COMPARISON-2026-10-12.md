# ZX-UX v1 historical visual comparison checkpoint

The checked old-SDK reference archive and the archived historical SDK
sources were compared against 48 actual ZX-UX native emulator screenshots.
Each record includes source/image hashes and capture paths in
`docs/step5-v1-frame-comparisons.json`.

There are 48 pairs. Fourteen pairs have identical active-screen pixels;
33 pairs have different active-screen pixels; one pair uses different
source bytes. In all, 34 comparisons contain 16,537 differing pixels.
The historical and current C48 source bytes match for 47 of the 48 pairs.

Old reference screenshots at 768 by 576 were reduced to 256 by 192 only
when exact threefold pixel replication was verified. One historical image
was already at 256 by 192. Current emulator screenshots were cropped to
the 256 by 192 active display only after verifying the doubled pixel
replication and capture borders. Every counted difference comes from
actual image bytes, not a reconstructed historical screenshot.

Historical frame timing, keyboard input, and random state are not fully
recorded. Therefore all 48 comparisons remain inconclusive as behavioral
compatibility tests, including the 14 pairs with identical pixels.
This does not prove or disprove native visual equivalence. The separate
30-image old-kernel historical proof set still needs matched native states.

The checked image difference masks, detailed JSON, and comparison method
are preserved in the private Library under
`/ZX-UX/handover-20261012/visual-native-48/`. The original historical
images are not added to the current source or release tree. A genuine
matched-state run is still required before any visual case is a pass.

Final v1 release approval remains pending.

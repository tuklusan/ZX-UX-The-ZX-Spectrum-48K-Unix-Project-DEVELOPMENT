MINELAY — C48 translation of historical Spectrum BASIC program 01.
Original: ../BASIC/01-minelay.bas and original TZX/screenshots (untouched).

Controls: ENTER after animated title; 1 = hard, 2 = easy;
Q/Z = up/down, I/P = left/right. Collect yellow eggs (+10), avoid
blue mines and the moving mine-layer; an axe permits one protected
collision or destroys an interior maze wall. One reserve life is gained
at each 500-point threshold. The initial three lives display as two
reserve icons. After lives are depleted, the game-over menu shows the
score/high score (including a new-record message), then restarts.

Source mapping: BASIC 50-150 -> player loop and collisions; 700-940 ->
mine-layer half-cell pursuit and mine/egg/axe drops; 5000-6007 -> axe,
life loss and respawn; 6020-6050 -> game over and choice menu;
7000-7850 -> maze and game state; 9000-9040 -> original 56 glyph bytes;
9500-9999 -> moving title, instructions and ENTER start.
The frozen c48lib supplies 32x24 display cells and 8x8 glyph rendering.
Build from the 60-program workspace with build/build-c48.py 01-minelay.
Published outputs: minelay.ssx and minelay.tzx (tape name: minelay).

Verification: program-specific test-minelay.py checks the original BASIC
source, all seven sprite glyphs, screen placement, life counts, RNG
thresholds, chase/trail ordering, title data, inverse game-over and
high-score message. Forced native-C logic tests exercise held/idle
movement, axe/wall interactions, protected hits, mine and pursuer life
loss, visible-cell collision timing, 500-point extra life and clearing
both old player and explosion cells. The actual frozen ZX-UX kernel was
executed through introduction, difficulty menu, movement, pursuit,
life depletion, stable game over and hard restart; successive frames
were inspected for duplicate pursuers. The actual TZX was inserted into
the frozen machine, and its shell's 'yolo' command invoked the native
loader; cassette consumption, SSX-load syscall and title glyphs were
observed. Genuine resulting captures are under C48/SCREENSHOTS/.

Intended source-equivalent presentation differences: C48 uses the
shared Acer VGA text font instead of the Spectrum ROM lettering.
RNG sequence, audio pitch/duration and frame pacing are approximate
because the frozen SDK and BASIC runtime differ. Compare equivalent
visible states, not identical random layouts or absolute capture time.
No historical BASIC, frozen SDK, kernel or emulator source was modified.

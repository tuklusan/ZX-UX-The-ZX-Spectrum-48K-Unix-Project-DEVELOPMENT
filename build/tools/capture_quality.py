"""Screen-only checks for native RVM and Fuse screenshots.

These checks reject known boot/partial frames; they do not certify gameplay.
"""
from __future__ import annotations


def bitmap_ink(screen: bytes) -> int:
    """Only count Spectrum bitmap pixels, never paper or border colour."""
    if len(screen) != 6912:
        raise ValueError('invalid Spectrum display memory')
    return sum(v.bit_count() for v in screen[:6144])


def distinct_pixels(image, reference, threshold=32):
    """Number of changed pixels inside the native 256x192 display."""
    from PIL import ImageChops
    if image.size != (320, 240) or reference.size != image.size:
        raise ValueError('incorrect Fuse screen crop')
    current = image.convert('RGB').crop((32, 24, 288, 216)).resize((64, 48))
    previous = reference.convert('RGB').crop((32, 24, 288, 216)).resize((64, 48))
    delta = ImageChops.difference(current, previous)
    return sum(max(pixel) > threshold for pixel in delta.get_flattened_data())


class StableFrames:
    """Prefer persistent, developed pictures over high-ink transient frames.

    Moving screens may be retained as candidates, but persistence is mandatory
    when a static drawing has been requested. No pixels are altered.
    """
    def __init__(self, boot, shell=None, *, stable_samples=4, min_change=12):
        self.baselines = (boot,) if shell is None else (boot, shell)
        self.stable_samples = stable_samples
        self.min_change = min_change
        self.previous = None
        self.persisted = 0
        self.best_stable = None
        self.stable_score = float('-inf')
        self.best_live = None
        self.live_score = float('-inf')
        self.accepted = 0

    def observe(self, frame, score):
        if any(distinct_pixels(frame, ref) < self.min_change for ref in self.baselines):
            self.previous = None
            self.persisted = 0
            return False
        # Solid paper can score highly even when there is no game picture.
        native = frame.convert('RGB').crop((32, 24, 288, 216))
        if native.resize((128, 96)).getcolors(maxcolors=1) is not None:
            self.previous = None
            self.persisted = 0
            return False
        if score <= 0:
            self.previous = None
            self.persisted = 0
            return False
        self.accepted += 1
        if score > self.live_score:
            self.best_live, self.live_score = frame.copy(), score
        if self.previous is not None and distinct_pixels(frame, self.previous, threshold=20) <= 8:
            self.persisted += 1
        else:
            self.persisted = 1
        self.previous = frame.copy()
        if self.persisted >= self.stable_samples and score > self.stable_score:
            self.best_stable, self.stable_score = frame.copy(), score
        return True

    def result(self, *, require_stable=False):
        if self.best_stable is not None:
            # A stable completed image wins over a transient with extra ink.
            return self.best_stable
        if require_stable:
            raise RuntimeError('no persistent completed native screen observed')
        if self.best_live is None:
            raise RuntimeError('no distinct native program screen observed')
        return self.best_live


def program_output_lines(current: str, shell: str) -> set[str]:
    """New console rows, excluding ZX-UX command, loader and taskbar rows.

    The login banner persists after an ordinary tty program prints. Its
    presence cannot reject native program output; a new row can be anywhere.
    """
    def lines(text: str) -> set[str]:
        found = set()
        for row in text.splitlines():
            value = row.strip()
            low = value.lower()
            if (not value or value in ('#', '@')
                    or low.startswith(('loading: /dev/cassette/',
                                       '# /dev/cassette/',
                                       '@ /dev/cassette/'))
                    or ('1.init' in low and '2.sh' in low)):
                continue
            found.add(value)
        return found

    return lines(current) - lines(shell)

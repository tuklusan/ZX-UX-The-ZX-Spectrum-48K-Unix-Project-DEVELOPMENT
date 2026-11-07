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


def moving_replay_frame(frames, boot, shell, *, minimum_change=18):
    """Choose a real moving native frame rather than a settled menu.

    Three adjacent changes and two visible ink colours are required. The
    returned image is never altered; an unobserved moving scene is refused.
    """
    from PIL import ImageChops
    if len(frames) < 5:
        return None
    areas = [image.convert('RGB').crop((32, 24, 288, 192)) for image in frames]
    changes = [sum(max(pixel) > 60 for pixel in
                   ImageChops.difference(left, right).get_flattened_data())
               for left, right in zip(areas, areas[1:])]
    run = 0
    selected = None
    richest_ink = -1
    for index in range(1, len(frames) - 1):
        if min(changes[index - 1], changes[index]) < minimum_change:
            run = 0
            continue
        if any(distinct_pixels(frames[index], baseline) < 12
               for baseline in (boot, shell)):
            run = 0
            continue
        colours = areas[index].getcolors(maxcolors=256 * 192) or ()
        visible = sum(count >= 5 for count, rgb in colours if max(rgb) > 65)
        if visible < 2:
            run = 0
            continue
        run += 1
        if run >= 3:
            # Among verified moving frames, keep the most developed scene.
            # Later sparse or partially cleared displays must not erase it.
            ink = sum(max(pixel) > 65 for pixel in
                      areas[index].get_flattened_data())
            if ink >= richest_ink:
                selected, richest_ink = frames[index], ink
    return selected


def recorded_result_frame(frames, before, boot, shell, *, stable_samples=3):
    """Choose a settled post-key image without assuming random games move.

    A real, persistent changed screen is required. Input alone, a blank
    frame, an unchanged prompt, and an unobserved result never pass.
    """
    if len(frames) < stable_samples:
        return None
    selection = StableFrames(boot, shell, stable_samples=stable_samples)
    for frame in frames:
        if distinct_pixels(frame, before) < 12:
            selection.previous = None
            selection.persisted = 0
            continue
        native = frame.convert('L').crop((32, 24, 288, 216))
        ink = sum(v > 48 for v in native.resize((80, 60)).get_flattened_data())
        selection.observe(frame, ink)
    return selection.best_stable

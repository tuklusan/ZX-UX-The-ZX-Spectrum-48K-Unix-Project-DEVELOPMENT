"""Convert verified HiSoft direct word patches into source-owned operands.

A patched source word is eligible only when all three real compiler passes
agree on its type, site, and relocated target. Unknown spans stay unresolved.
This step never decodes instructions from the linked program.
"""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from symbolic_source_patches import from_emissions, verify_three_passes


class PatchBindingError(ValueError):
    """A source word patch cannot replace its original emission exactly."""


def _bind_one(events, image: bytes, words):

    direct = [e for e in events if e.kind == 'direct-write']
    expected = {offset for word in words for offset in (word.site, word.site + 1)}
    actual = [e.position + i for e in direct for i in range(len(e.data))]
    if len(actual) != len(expected) or set(actual) != expected:
        raise PatchBindingError('unowned or repeated direct source write')
    originals = list(events)
    replacements = {}
    for word in words:
        site = word.site
        if not 0 <= site < len(image) - 1:
            raise PatchBindingError('source patch outside image')
        writers = [(i, e) for i, e in enumerate(originals)
                   if e.kind != 'direct-write' and e.position <= site and
                   e.position + len(e.data) > site]
        if len(writers) != 1:
            raise PatchBindingError('patch has no unique original source word')
        index, event = writers[0]
        if (event.kind != 'word' or event.position != site or len(event.data) != 2 or
                index in replacements):
            raise PatchBindingError('patch does not replace a whole source word')
        # Require the whole original footprint to be owned by the same event.
        if any(other is not event and other.kind != 'direct-write' and
               other.position < site + 2 and
               other.position + len(other.data) > site
               for other in originals):
            raise PatchBindingError('patch overlaps another original source')
        if image[site:site + 2] != word.value.to_bytes(2, 'little'):
            raise PatchBindingError('typed source word differs from final image')
        if word.kind == 'control-target':
            if not isinstance(word.target, int):
                raise PatchBindingError('control word lacks typed relocation')
            if index == 0:
                raise PatchBindingError('control operand has no original opcode')
            previous = originals[index - 1]
            if (previous.kind != 'opcode' or
                    previous.position + len(previous.data) != site or
                    previous.source.count('nn') != 1):
                raise PatchBindingError('control operand lacks adjacent source opcode')
            replacements[index] = replace(event, kind='relocation',
                                          source=str(word.target),
                                          data=image[site:site + 2],
                                          symbol_offset=word.target)
        elif word.kind == 'literal-length':
            replacements[index] = replace(event, kind='instruction',
                                          source=f'defw {word.value}',
                                          data=image[site:site + 2])
        else:
            raise PatchBindingError('unknown patched word type')
    return tuple(replacements.get(i, event) for i, event in enumerate(originals)
                 if event.kind != 'direct-write')


def bind_three_source_passes(groups, images, bases, text_ends):
    """Bind only cross-pass verified source patches; preserve all other events."""
    if (len(groups) != 3 or len(images) != 3 or len(bases) != 3 or
            len(text_ends) != 3 or len(set(bases)) != 3):
        raise PatchBindingError('three distinct compiler passes required')
    words = [from_emissions(events, image, base, end)
             for events, image, base, end in zip(groups, images, bases, text_ends)]
    report = verify_three_passes(words, [SimpleNamespace(base=b) for b in bases])
    bound = tuple(_bind_one(events, image, patch_words)
                  for events, image, patch_words in zip(groups, images, words))
    report['bound_source_word_bytes'] = 2 * len(words[0])
    return bound, report

"""Release the separate historical BASIC-to-C48 hand-ported programs."""
from pathlib import Path
import shutil
import sys

SDK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SDK))
from rb2ct.driver import PORTS, available, build


def package(stage: Path):
    names = available()
    if names != ['01-minelay', '25-galaxians', '58-invaders']:
        raise RuntimeError('historical BASIC-to-C48 ports are incomplete')
    source_out = stage / 'assets/rb2ct-src'
    shutil.copytree(PORTS, source_out)
    ssx_dir = stage / 'assets/rb2ct-bin/ssx'
    tzx_dir = stage / 'assets/rb2ct-bin/tzx'
    ssx_dir.mkdir(parents=True)
    tzx_dir.mkdir(parents=True)
    for name in names:
        working = stage / 'assets/rb2ct-bin/tmp'
        working.mkdir(parents=True, exist_ok=True)
        sources = list((source_out / '60-programs' / name / 'C48').glob('*.c'))
        if len(sources) != 1:
            raise ValueError(name + ': missing hand-translated source')
        ssx, tzx = build(sources[0], source_out / 'c48lib', working)
        shutil.move(str(ssx), ssx_dir / ssx.name)
        shutil.move(str(tzx), tzx_dir / tzx.name)
    working.rmdir()
    return len(names)

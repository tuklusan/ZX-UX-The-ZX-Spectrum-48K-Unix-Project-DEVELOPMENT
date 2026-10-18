#!/usr/bin/env python3
"""Build everything: python3 release/build/build.py [sjasmplus]."""
import pathlib, re, shutil, subprocess, sys
sys.dont_write_bytecode = True
R = pathlib.Path(__file__).resolve().parents[1]; B, S, D = R/'build', R/'src', R/'dist'
sys.path.insert(0, str(S/'zx-ux-sdk/tools'))
import osbuild, turbo_boot_build, c48build, sdkpack
argv = sys.argv[1:]; argv = argv[1:] if argv[:1] == ['--sjasm'] else argv
sjasm = str(pathlib.Path(argv[0]).resolve()) if len(argv)==1 else shutil.which('sjasmplus') or 'sjasmplus'
# C48 program sources are part of the distributed kit. Stage them before
# replacing dist, so a failed build cannot discard its own input collection.
corpus = D/'assets/c48-src'
if not corpus.is_dir() or corpus.is_symlink():
    raise RuntimeError('Missing distributed C48 program sources: ' + str(corpus))
if any(p.is_symlink() for p in corpus.rglob('*')):
    raise RuntimeError('Linked C48 source paths are not supported')
for name in ('src', 'sdk', 'out', 'dist-new'): shutil.rmtree(B/name, ignore_errors=True)
shutil.copytree(corpus, B/'dist-new/assets/c48-src')
shutil.copytree(S/'zx-ux', B/'src'); shutil.copytree(S/'zx-ux-sdk', B/'sdk')
(B/'out').mkdir(); (B/'sdk/rom').mkdir(exist_ok=True)
for name, folder in (('48.rom','rom'), ('font4x8.bin','')): shutil.copy2(S/'zx-ux'/folder/name, B/'sdk/rom'/name)
subprocess.run([sys.executable, str(S/'zx-ux-sdk/tools/osbuild.py'), sjasm], check=True)
syms = dict((m.group(1), int(m.group(2),16)) for line in (B/'src/unix.sym').read_text().splitlines() if (m := re.match(r'(\S+): EQU 0x([0-9A-Fa-f]+)', line)))
_, _, free, _ = osbuild.mkfs(syms, osbuild.program_list()); turbo_boot_build.create_tzx(sjasm, syms, syms['kend']-0x6000, free, output_name='ZX-UX.tzx')
(B/'dist-new/zx-ux').mkdir(parents=True)
shutil.copy2(B/'out/ZX-UX.tzx', B/'dist-new/zx-ux/ZX-UX.tzx')
c48build.build(B/'sdk', B/'dist-new/assets/c48-src', B/'dist-new/assets/c48-bin'); sdkpack.pack(S/'zx-ux-sdk', S/'zx-ux', B, B/'dist-new/sdk/bin')
shutil.rmtree(B/'dist-old', ignore_errors=True)
if D.exists(): D.rename(B/'dist-old')
try:
    (B/'dist-new').rename(D)
except BaseException:
    if not D.exists() and (B/'dist-old').exists():
        (B/'dist-old').rename(D)
    raise
shutil.rmtree(B/'dist-old', ignore_errors=True)

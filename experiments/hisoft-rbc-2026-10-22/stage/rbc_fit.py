"""Install native RBC defaults, memory sizing, and RCC-compatible output modes.

The standard Spectrum ROM already holds 768 printable font bytes. With the
frozen 48K ROM, ordinary BASIC can point CHARS there instead of carrying a
second full copy. Programs that edit printable glyphs keep their private bank.
No code backend is invented: RBC still emits native HiSoft machine code.
"""
from __future__ import annotations


def patched(source: str) -> str:
    """Patch the exact preserved RBC source, rejecting an unfamiliar revision."""
    def change(before, after):
        nonlocal source
        if source.count(before) != 1:
            raise ValueError('RBC structure changed; review fit and output generation')
        source = source.replace(before, after, 1)

    change('from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize',
           'from rbc_output import output_path, memory_required, write_mode\n'
           'from memory_safety import MemoryBlocked, analyze_lines, enforce, summarize')
    change('def build_ssx(builds: list[HiSoftBuild], font:bytes, rld,\n'
           '              stack:int=384) -> tuple[bytes,dict]:',
           'def build_ssx(builds: list[HiSoftBuild], font:bytes, rld,\n'
           '              stack:int=384, use_rom_font=False) -> tuple[bytes,dict]:')
    change('font_start=len(e.code);e.code.extend(font)',
           'font_start=len(e.code)\n'
           '    if not use_rom_font:\n'
           '        e.code.extend(bytes(256))\n'
           '        e.code.extend(font)')
    change('(fontptr,font_start-256),(udgptr,udg_start)',
           '(fontptr,0x3C00 if use_rom_font else font_start),(udgptr,udg_start)')
    change('    reloc=sorted(e.fixups)',
           '    if use_rom_font:\n'
           '        e.fixups.remove(fontptr)\n'
           '    reloc=sorted(e.fixups)')
    change("'font_bytes':len(font),'udg_bytes':21*8,",
           "'font_bytes':0 if use_rom_font else len(font)+256,'udg_bytes':21*8,\n"
           "                 'font_source':'spectrum_rom' if use_rom_font else 'process_image',")
    change("ap.add_argument('-o','--output',type=Path,required=True,help='target SSX1 executable')",
           "ap.add_argument('-o','--output',type=Path,help='output path (default: next to BASIC input)')\n"
           "    ap.add_argument('-S',action='store_true',dest='assembly_only',help='emit Z80 assembly')\n"
           "    ap.add_argument('-c',action='store_true',dest='object_only',help='emit SSO1 object')\n"
           "    ap.add_argument('--fit',action='store_true',default=True,dest='fit',\n"
           "                    help='use 48K ROM glyphs to save native image memory (default)')\n"
           "    ap.add_argument('--no-fit',action='store_false',dest='fit',\n"
           "                    help='retain the embedded character font')\n"
           "    ap.add_argument('--max',type=lambda n:int(n,0),default=11000,\n"
           "                    help='maximum image, data and stack bytes (0 disables)')\n"
           "    ap.add_argument('--native',action='store_true',help='force the existing native backend')\n"
           "    ap.add_argument('--bytecode',action='store_true',\n"
           "                    help='unsupported: no BASIC bytecode backend exists')\n"
           "    ap.add_argument('--heap',type=lambda n:int(n,0),default=None)\n"
           "    ap.add_argument('--udgs',type=lambda n:int(n,0),default=None)")
    change('    args=ap.parse_args(argv)\n    try:',
           "    args=ap.parse_args(argv)\n"
           "    if args.assembly_only and args.object_only:\n"
           "        ap.error('conflicting output modes')\n"
           "    if args.tzx and (args.assembly_only or args.object_only):\n"
           "        ap.error('cassette output requires linked SSX')\n"
           "    if args.bytecode:\n"
           "        ap.error('--bytecode is unavailable for native RBC')\n"
           "    if args.heap is not None:\n"
           "        ap.error('--heap is not adjustable in RBC')\n"
           "    if args.udgs is not None and args.udgs != 21:\n"
           "        ap.error('--udgs must be 21 for Sinclair BASIC')\n"
           "    if args.max < 0 or args.stack < 1:\n"
           "        ap.error('--max must be nonnegative and --stack positive')\n"
           "    mode = 'assembly' if args.assembly_only else 'object' if args.object_only else 'link'\n"
           "    args.output = output_path(args.source, args.output, mode)\n"
           "    if args.source.is_file() and args.output.exists() and args.source.samefile(args.output):\n"
           "        ap.error('output would overwrite the BASIC input')\n"
           "    try:")
    change('        ssx,diagnostics=build_ssx(builds,font,rld,args.stack)',
           "        ssx,diagnostics=build_ssx(builds,font,rld,args.stack,\n"
           "               use_rom_font=args.fit and not meta.get('private_font_requested',False))\n"
           "        measured = memory_required(rld.parse_ssx(ssx), len(ssx))\n"
           "        diagnostics['memory_required'] = measured\n"
           "        diagnostics['memory_limit'] = args.max\n"
           "        diagnostics['fit_default'] = args.fit\n"
           "        if mode == 'link' and args.max and measured > args.max:\n"
           "            if args.report:\n"
           "                args.report.parent.mkdir(parents=True,exist_ok=True)\n"
           "                args.report.write_text(json.dumps({'compile':'too_large',\n"
           "                    'cause_category':'native-memory-limit',\n"
           "                    'memory_required':measured,'memory_limit':args.max,\n"
           "                    'source':str(args.source),'image':diagnostics['image'],\n"
           "                    'bss':diagnostics['bss'],'stack':args.stack},indent=2)+'\\n')\n"
           "            raise ValueError('%s needs %d bytes of native memory (limit %d)'\n"
           "                             % (args.source,measured,args.max))")
    change("        args.output.write_bytes(ssx)",
           "        if mode == 'object':\n"
           "            import ras\n"
           "            write_mode(args.output,ssx,mode,rld,ras)\n"
           "        else:\n"
           "            write_mode(args.output,ssx,mode,rld)")

    change('        if args.report:\n            args.report.write_text(json.dumps(meta,indent=2)+\'\\n\')',
           "        if args.report:\n"
           "            args.report.parent.mkdir(parents=True,exist_ok=True)\n"
           "            args.report.write_text(json.dumps(meta,indent=2)+'\\n')")
    change('byte SSX1 ({diagnostics["relocations"]} relocations)',
           'byte {mode} ({diagnostics["relocations"]} relocations)')
    return source

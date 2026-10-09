#!/usr/bin/env python3
"""rvm - the ZX-UX virtual machine: run an SSX1 C48 program on the host.

The program runs on an emulated Z80 with the real 48K ROM; the ZX-UX kernel's
system-call interface (call 6003h) is emulated in Python, including the C
support calls (ticks, screen).  Floats and BEEP are the program's own calls
into the ROM, run here as on the Spectrum.  What runs is the same SSX1 file
that goes to tape.

  rvm.py prog.ssx [args...] [--keys TEXT] [--frames N] [--scr F] [--png F]
         [--text] [--root DIR] [--ticks N] [--load ADDR] [--trace]

  --keys TEXT   keyboard input for getchar (\\n = ENTER); end of input ends
                the run (status 'input')
  --frames N    stop after N emulated 50 Hz frames (default 3000)
  --scr/--png   write the final screen (6912-byte .scr / PNG)
  --text        print the final screen as text
  --ticks N     fixed value returned by ticks() (deterministic runs)
  --root DIR    host directory for open()/read()
"""
import os
import sys
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

from skoolkit import CSimulator, ROM48, read_bin_file   # noqa: E402
from skoolkit.simutils import from_memory               # noqa: E402
import rld                                               # noqa: E402

FRAME = 69888
SYS = 0x6003
FONT = 0x5E00
EINVAL, ENOENT, EBADF, EIO = 22, 2, 9, 5
NAMES = {0: 'rele', 1: 'exit', 3: 'read', 4: 'write', 5: 'open', 6: 'close',
         17: 'break', 19: 'seek', 31: 'stty', 32: 'gtty', 34: 'sleep', 36: 'getpid',
         38: 'ticks', 39: 'screen'}


def font_bytes():
    p = os.path.join(HERE, '..', 'src', 'font4x8.bin')
    return open(p, 'rb').read()[8:8 + 384]


class Stop(Exception):
    def __init__(self, why, status=0):
        self.why = why
        self.status = status


class Tracer:
    def __init__(self):
        self.border = 0
        self.spk = 0
        self.edges = 0          # speaker (EAR/MIC bit 4) changes: BEEP

    def read_port(self, registers, port):
        return 0xFF

    def write_port(self, registers, port, value, *rest):
        if not port & 1:
            self.border = value & 7
            if (value ^ self.spk) & 0x10:
                self.edges += 1
            self.spk = value


class VM:
    def __init__(self, ssx, args=(), keys=b'', root=None, fixed_ticks=None, load=0x8000):
        hdr = rld.parse_ssx(ssx)
        self.hdr = hdr
        mem = [0] * 65536
        rom = read_bin_file(ROM48)
        mem[:len(rom)] = rom
        mem[FONT:FONT + 384] = list(font_bytes())
        img = rld.relocate(hdr['image'], hdr['relocs'], load)
        mem[load:load + len(img)] = list(img)
        end = load + len(img) + hdr['bss'] + hdr['heap']
        argv0 = [b'prog'] + [a.encode() for a in args]
        # as ZX-UX's loader: image, bss, heap, stack, then the arguments
        top = load + max(len(img) + hdr['bss'] + hdr['heap'] + hdr['stack'], len(ssx)) \
            + sum(len(a) + 1 for a in argv0) + 2 * len(argv0) + 6
        if top > 0x10000:
            raise SystemExit('rvm: program does not fit (needs %d bytes)' % (top - load))
        top = min(top, 0x10000)
        # arguments (ZX-UX exec layout): SP -> argc, argv..., 0, strings
        argv = [b'prog'] + [a.encode() for a in args]
        strs = b''.join(a + b'\0' for a in argv)
        sp = (top - len(strs)) & 0xFFFE
        mem[sp:sp + len(strs)] = list(strs)
        ptrs = []
        p = sp
        for a in argv:
            ptrs.append(p)
            p += len(a) + 1
        vec = [len(argv)] + ptrs + [0]
        sp -= 2 * len(vec)
        for i, v in enumerate(vec):
            mem[sp + 2 * i] = v & 255
            mem[sp + 2 * i + 1] = v >> 8
        self.load = load
        self.top = top
        self.brk = end
        self.sim = from_memory(CSimulator, mem, {'SP': sp, 'PC': load + hdr['entry'], 'IY': 0x5C3A},
                               {'iff': 0, 'im': 1})
        self.mem = self.sim.memory
        self.tr = Tracer()
        self.sim.set_tracer(self.tr)
        self.keys = list(keys)
        self.fixed_ticks = fixed_ticks
        self.root = root
        self.files = {}
        self.out = bytearray()
        self.screen_owned = False
        self.tbase = 0
        self.syscalls = 0

    # ------------------------------------------------------------ memory
    def rd(self, a):
        return self.mem[a] | self.mem[a + 1] << 8

    def wr(self, a, v):
        self.mem[a] = v & 255
        self.mem[(a + 1) & 0xFFFF] = (v >> 8) & 255

    def cstr(self, a):
        out = bytearray()
        while self.mem[a]:
            out.append(self.mem[a])
            a += 1
        return bytes(out)

    def frames(self):
        return (self.sim.registers[25] + self.tbase) // FRAME

    # ------------------------------------------------------------ run
    def run(self, max_frames=3000, trace=False):
        r = self.sim.registers
        limit = max_frames * FRAME
        try:
            while True:
                t = r[25] + self.tbase
                if t >= limit:
                    raise Stop('frames')
                self.sim.trace(r[24], SYS, 0, min(r[25] + FRAME, limit - self.tbase), 0,
                               None, None, None, None, None)
                if r[24] == SYS:
                    self.syscall(trace)
        except Stop as s:
            self.status = s.status
            return s.why

    def syscall(self, trace):
        r = self.sim.registers
        a = r[0]
        hl = r[6] << 8 | r[7]
        de = r[4] << 8 | r[5]
        bc = r[2] << 8 | r[3]
        self.syscalls += 1
        if trace:
            print('sys %s(%d) hl=%04x de=%04x bc=%04x' % (NAMES.get(a, '?'), a, hl, de, bc), file=sys.stderr)
        err = None
        res = 0
        if a == 0:                       # rele / yield
            pass
        elif a == 1:                     # exit
            raise Stop('exit', hl & 255)
        elif a == 3:                     # read
            if hl == 0:
                if not self.keys:
                    raise Stop('input')
                n = 0
                while n < bc and self.keys:
                    self.mem[de + n] = self.keys.pop(0)
                    n += 1
                    break
                res = n
            elif hl in self.files:
                f = self.files[hl]
                data = f['data'][f['pos']:f['pos'] + bc]
                self.mem[de:de + len(data)] = list(data)
                f['pos'] += len(data)
                res = len(data)
            else:
                err = EBADF
        elif a == 4:                     # write
            data = bytes(self.mem[de:de + bc])
            if hl in (1, 2):
                self.out += data
                res = bc
            else:
                err = EBADF
        elif a == 5:                     # open
            name = self.cstr(hl).decode('latin-1')
            path = os.path.join(self.root or '.', name.lstrip('/'))
            if self.root is None or not os.path.isfile(path):
                err = ENOENT
            else:
                fd = 3
                while fd in self.files:
                    fd += 1
                self.files[fd] = {'data': open(path, 'rb').read(), 'pos': 0}
                res = fd
        elif a == 6:                     # close
            if self.files.pop(hl, None) is None and hl > 2:
                err = EBADF
        elif a == 17:                    # break
            if hl < self.brk or hl > self.top - 256:
                err = 12
            else:
                self.brk = hl
        elif a == 19:                    # seek
            f = self.files.get(hl)
            if f is None:
                err = EBADF
            else:
                base = (0, f['pos'], len(f['data']))[bc] if bc in (0, 1, 2) else 0
                f['pos'] = max(0, base + (de - 65536 if de >= 32768 and bc else de))
                res = f['pos'] & 0xFFFF
        elif a in (31,):                 # stty
            pass
        elif a == 32:                    # gtty
            for i in range(6):
                self.mem[de + i] = 0
            self.mem[de + 4] = 0x10
        elif a == 34:                    # sleep (ticks)
            self.tbase += hl * FRAME
        elif a == 36:
            res = 1
        elif a == 38:                    # ticks
            if self.fixed_ticks is not None:
                res = self.fixed_ticks
            else:
                res = self.frames() & 0xFFFF
            r[4] = r[5] = 0
        elif a == 39:                    # screen
            self.screen_owned = bool(hl)
            res = FONT if hl else 0
            r[4] = r[5] = 0                 # DE = 0: the only owner
        else:
            err = EINVAL
        # return from the call: result in HL, CF/A on error
        if err is not None:
            r[6], r[7] = 0xFF, 0xFF
            r[0] = err
            r[1] |= 1
        else:
            r[6], r[7] = (res >> 8) & 255, res & 255
            r[1] &= ~1
            r[0] = 0
        sp = r[12]
        r[24] = self.rd(sp)
        r[12] = (sp + 2) & 0xFFFF
        r[25] += 200                      # system call overhead

    # ------------------------------------------------------------ output
    def screen(self):
        return bytes(self.mem[0x4000:0x5B00])


def screen_text(scr, font=None):
    fb = font or font_bytes()
    glyphs = {}
    for c in range(32, 128):
        g = fb[(c - 32) * 4:(c - 32) * 4 + 4]
        rows = bytes(n for b in g for n in (b >> 4, b & 15))
        glyphs.setdefault(rows, chr(c))
        glyphs.setdefault(bytes(15 - x for x in rows), chr(c))
    lines = []
    for row in range(24):
        s = ''
        for col in range(64):
            a = ((row & 0x18) << 8) + ((row & 7) << 5) + col // 2
            sh = 4 if col % 2 == 0 else 0
            g = bytes((scr[a + (i << 8)] >> sh) & 15 for i in range(8))
            s += glyphs.get(g, '#' if any(g) else ' ')
        lines.append(s.rstrip())
    return '\n'.join(lines)


def write_png(scr, fname, border=0, scale=2, bw=16):
    import zlib
    pal = [(0, 0, 0), (0, 0, 205), (205, 0, 0), (205, 0, 205), (0, 205, 0), (0, 205, 205), (205, 205, 0), (205, 205, 205),
           (0, 0, 0), (0, 0, 255), (255, 0, 0), (255, 0, 255), (0, 255, 0), (0, 255, 255), (255, 255, 0), (255, 255, 255)]
    W, H = 256 + 2 * bw, 192 + 2 * bw
    bc = pal[border & 7]
    rows = []
    for y in range(H):
        row = []
        sy = y - bw
        for x in range(W):
            sx = x - bw
            if 0 <= sx < 256 and 0 <= sy < 192:
                a = ((sy & 0xC0) << 5) | ((sy & 7) << 8) | ((sy & 0x38) << 2) | (sx >> 3)
                at = scr[6144 + (sy >> 3) * 32 + (sx >> 3)]
                bit = scr[a] >> (7 - (sx & 7)) & 1
                br = 8 if at & 0x40 else 0
                ink, pap = (at & 7) + br, ((at >> 3) & 7) + br
                row.append(pal[ink if bit else pap])
            else:
                row.append(bc)
        row = [c for c in row for _ in range(scale)]
        for _ in range(scale):
            rows.append(row)
    raw = b''.join(b'\0' + bytes(v for c in r for v in c) for r in rows)

    def chunk(t, d):
        c = struct.pack('>I', len(d)) + t + d
        return c + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    png = (b'\x89PNG\r\n\x1a\n' +
           chunk(b'IHDR', struct.pack('>IIBBBBB', W * scale, H * scale, 8, 2, 0, 0, 0)) +
           chunk(b'IDAT', zlib.compress(raw, 9)) + chunk(b'IEND', b''))
    open(fname, 'wb').write(png)


def main(argv):
    opts = {'--keys': None, '--frames': '3000', '--scr': None, '--png': None, '--root': None,
            '--ticks': None, '--load': '0x8000'}
    flags = set()
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in opts:
            opts[a] = argv[i + 1]
            i += 2
            continue
        if a in ('--text', '--trace'):
            flags.add(a)
            i += 1
            continue
        pos.append(a)
        i += 1
    if not pos:
        print(__doc__)
        return 2
    keys = (opts['--keys'] or '').encode().decode('unicode_escape').encode('latin-1')
    vm = VM(open(pos[0], 'rb').read(), pos[1:], keys, opts['--root'],
            int(opts['--ticks']) if opts['--ticks'] else None, int(opts['--load'], 0))
    why = vm.run(int(opts['--frames']), '--trace' in flags)
    scr = vm.screen()
    if opts['--scr']:
        open(opts['--scr'], 'wb').write(scr)
    if opts['--png']:
        write_png(scr, opts['--png'], vm.tr.border)
    if '--text' in flags:
        print(screen_text(scr))
    if vm.out:
        sys.stdout.write(vm.out.decode('latin-1'))
    print('rvm: stopped (%s) status %d after %d frames, %d system calls, %d speaker edges'
          % (why, vm.status, vm.frames(), vm.syscalls, vm.tr.edges), file=sys.stderr)
    return vm.status if why == 'exit' else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))

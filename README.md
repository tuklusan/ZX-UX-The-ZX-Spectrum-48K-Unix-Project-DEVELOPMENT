# RETRO UNIX Z80 v1 — UNIX v1 for the ZX Spectrum 48K

A fresh Z80 implementation of **Retro UNIX 8086 v1** (Erdogan Tan's 8086 re-creation of the 1971 PDP-11 UNIX v1), running on a stock 48K ZX Spectrum. The 8086 and PDP-11 sources were used as a specification only: every kernel routine and every program was analysed and rewritten for the Z80, with the Spectrum ROM doing the keyboard, screen, sound and tape work.

`build/runixz80.tzx` loads from tape straight into `login:`; log in and you are at the v1 shell prompt with the Retro UNIX user-land, plus `vi`, `ps` and `top`. Up to 4 processes run preemptively, switched by the Spectrum's 50 Hz interrupt.

**runix 2.0** replaces the fixed RAM disk and swap pool with one *elastic* memory arena: files, directories and process images all live in it and grow and shrink as needed (zxpack still compresses idle files). It also runs **C programs from cassette**. They are compiled on the host by the runix SDK (`sdk/`: compiler, linker, tape writer and a virtual machine), and run with:

```
/dev/cassette/chess
```

The tape is played after typing the command. The kernel finds the program, relocates it into the arena, and lends it the 4 KB window of the resident commands if it needs that much. The whole C48 SDK corpus (56 programs: games, demos, apps) runs this way. See *C programs* below, `sdk/README.md`, and the specifications in `docs/` (`SPEC-ELASTIC-R2.md`, `SPEC-SDK-R2.md`).

**runix 2.1** lets programs run side by side: several C programs share the screen (`hanoi` and `queens8` draw one half each), and a program started with `&` leaves the shell working below its picture, on text rows 21–22 with the status line on row 23. `build/runixz80-multitask.z80` is a snapshot with hanoi and queens8 already running (`tools/mtsnap.py`).

**runix 2.2** makes C programs smaller: the runtime library is linked routine by routine, a bytecode program carries only the interpreter handlers it uses, string literals are shared, range checks compile to one compare, and the UDG bank comes only with programs that use UDGs. hanoi and queens8 together shrink from 13,381 to 10,396 bytes and now run side by side without borrowing the window, so the shell stays live. The loader compacts the arena before placing a program.

## Using it

Load the tape (`LOAD ""` on a real machine, or open the TZX in any emulator set to 48K). The BASIC loader does `CLEAR 24575`, loads two code blocks and jumps to the kernel at 6000h. The kernel prints its banner, checks the root file system and starts `/etc/init`. As in v1, init forks `/etc/getty` (→ `/bin/login` → `/bin/sh`), waits for it, and forks a new one when you log out.

**Single user.** Any login name of 1–8 characters is accepted, with no password, and every user is the super-user (prompt `# `). The file system keeps the v1 mode bits so `ls -l` looks right, but they are not enforced; only the executable bit matters, because `exec` needs it. `/etc/passwd`, `passwd`, `su` and `chown` are gone, and the kernel no longer checks permissions or user ids at all.

| Key | Meaning |
|---|---|
| ENTER | end of line |
| DELETE (CAPS+0) | erase last character |
| EDIT (CAPS+1) | end of file (^D) — logs out of the shell |
| BREAK (CAPS+SPACE) | interrupt (v1 DEL): kills the foreground program |
| CAPS+2 | caps lock (UNIX is lower case) |
| SYM+A S D F G Y U | `~ \| \ { } [ ]` (no need for E mode) |
| SYM+B C V T R O 6 | `* ? / > < ; &` (standard Spectrum symbols) |

The screen is a 64 × 24 text terminal: 23 rows of text and, at the bottom, a status line drawn by the clock interrupt. The status line has a 12-column cell per process slot — slot number, state (`:` runnable, `.` sleeping, `z` zombie) and the 8-character program name — with the running process in inverse, then the time of day. A 4 × 8 block cursor blinks wherever a program is waiting for the keyboard.

## Memory map (48K, every byte used)

| Address | Use |
|---|---|
| 0000–3FFF | ROM — keyboard, BEEPER, SA/LD-BYTES, the float calculator for C programs, and the IM 2 vector (see below) |
| 4000–5AFF | display file: 64 × 24 text in a 4 × 8 font |
| 5B00–5BFF | printer buffer → kernel globals: process table (4 slots), open-file table, clock, tty state, arena state |
| 5C00–5CB5 | system variables (MEMBOT → time of day, print position, cursor, flags, tape scratch, zxpack encoder) |
| 5CCB–5CEA | dead BASIC area → i-node of a resident program |
| 5CEB–5EFF | dead BASIC/IF1 area → keyboard ring, process names, image scratch, zxpack model tail and coder state, kernel stack (360 bytes) |
| 5F01–5FFF | tty line buffer, zxpack state, exec argument buffer |
| 6000–7FEA | kernel (8,171 of 8,192 bytes, including the console driver, the zxpack compressor and the program loader) |
| 7FEC–816B | console font (4 × 8, 96 glyphs) |
| 816C–B0F8 | resident user-land text: user library + 37 programs |
| B0FA–B1F9 | the boot code as loaded (it runs once, outside the 8 KB kernel), then zxpack's literal model |
| B1FA–B4F9 | i-node table (24 i-nodes) |
| B4FA–EFFF | **the arena** (15,110 bytes): every file and directory, the image of every process, programs loaded from tape |
| F000–FFB8 | the window: data, bss and stack of the resident program that owns it — lent to the arena while a big program from tape runs |
| FFB9–FFF3 | u-area of the running process (59 bytes) |
| FFF4, FFFF | `JP isr` and `JR` — IM 2 trampoline |

The addresses below the arena are computed at build time from the size of the code.

**Interrupts.** IM 2 with `I = 39h`: the ROM is filled with FFh from 386Eh, so the vector is always FFFFh whatever is on the data bus. FFFFh holds `JR`; its offset is ROM byte 0000h (F3h = −13), landing on `JP isr` at FFF4h. This avoids a 257-byte table and keeps `I` out of 40h–7Fh, so real machines show no ULA "snow".

## The console — 64 columns in a 4 × 8 font

The kernel no longer prints through the ROM. `kputc` draws every character straight into the display file in a 4 × 8 font, two characters to a screen byte, which gives a 64 × 24 terminal much closer to a real UNIX one than the ROM's 32 columns.

* **Font.** 96 glyphs (20h–7Fh), packed two pixel rows to a byte, 384 bytes: the SANYALnet Labs 4 × 8 font from the ZX-UX c48 SDK (see the credits below).
* **Display file tricks.** The ULA's layout is used directly instead of computing addresses per pixel line. A character cell's address is `010rr000 rrrccccc` (row bits 4–3 and 2–0, column / 2). The 8 pixel lines of a cell are 256 bytes apart, so drawing a glyph is "write the nibble, `INC H`" eight times. Each nibble is merged with `xor (hl) / and mask / xor (hl)`, which leaves the neighbouring character alone. Scrolling moves 22 rows of 8 × 32-byte lines with `LDIR`, again stepping lines with `INC H`/`INC D`; the status row is never touched.
* **Control codes.** Printable ASCII, newline (with scrolling), backspace, tab (every 8 columns), bell (ROM BEEPER), form feed (clear screen), and the Spectrum's `AT row,col` (16h) and `INVERSE n` (14h), now for 23 rows and 64 columns. A line wraps after column 63.
* **Cursor.** The cursor is a 4 × 8 block XORed into the display file at the print position. As in the ZX-UX kernel, nothing but the bitmap changes, so taking it off restores the screen exactly. It is shown while a process waits in the tty driver and blinks from the clock interrupt every 16 frames (about 3 times a second). Before anything is drawn the cursor is taken off, and a "screen busy" flag stops the interrupt from blinking it halfway through a change, so it never leaves a mark.
* **Cost.** The driver (font rendering, scrolling, cursor and the new status line) took about 690 bytes of code. To keep the kernel within 8,192 bytes I dropped the ROM printing code and the `FRAMES` counter, and folded six copies of the namei + iget sequence into one helper. The kernel is now 7,786 bytes; the 384-byte font table sits right after it, next to the resident programs, as the ROM character set sat outside the kernel before.

`vi` uses the full 64 × 23 area and `od` prints v1's 8 words a line; everything else simply has more room.

## tar — files on cassette

```
tar cvf /dev/cassette/clive /usr/clive      start the recorder, then this
tar tvf /dev/cassette/clive                 list it   (start, then play)
tar xvf /dev/cassette/clive [file ...]      extract all, or some files
tap r|t|x [file ...]                        UNIX v1's name: tar c/t/x, verbose
```

* **Archives with labels.** The name after `/dev/cassette/` (up to 10 characters) labels the archive. One tape can hold several archives; `t` and `x` wind past the others to the one named, and `/dev/cassette` alone means the next one.
* **Full paths, directories, attributes.** Arguments are archived with their paths as given. A directory is archived with everything below it. Each file keeps its mode, size and modification time.
* **Packed files stay packed.** A file zxpack has packed goes to tape as its packed stream (half the tape time for text) and comes back packed: `tar` writes the stream and then marks the i-node packed in the kernel's i-node table through `/dev/mem`, the way v1's `icheck` and `clri` worked on the raw disk.
* **Extracting.** `x` replaces existing files without asking but says `replaced`, makes every directory a path needs, and removes a file again if memory runs out while it is written. With names, only those files and whatever lies below a named directory are extracted.
* **Tape format.** Ordinary Spectrum blocks, so any emulator's tape browser shows the names. An archive header carries the label, then for each file comes a header named after it and its data in blocks of up to 512 bytes, and an empty header ends the archive. A member's data starts with a preamble: kind, i-node flags, size, stored length, mtime and the path. Devices and the resident programs in `/bin` are not archived, since they are part of the system.
* **Cost.** About 1.8 KB of user-land code and no new kernel code except the header/data choice in the tape driver. Its 512-byte tape buffer keeps `tar`'s image small.

`/usr/doc/tar` is the manual page.

## zxpack — the kernel's file compressor

The arena holds more than its size in files, because the kernel keeps idle files packed and unpacks them only while they are in use. Nothing outside the kernel knows: `cat`, `vi` and `exec` always see the real contents, and `ls -l` shows the real size with a `z` in front.

* **Unpacking.** Any read or write of a packed file unpacks it first (`readi`/`writei` call `zunpack`): the stream is decoded into a new block of the file's size, which then replaces it. If there is no room, the file stays packed and intact.
* **Background packing.** When no process can run, the scheduler's idle loop packs closed files that have not been touched for 15 seconds. As soon as an interrupt makes a process runnable, packing gives up and the process runs.
* **Packing under pressure.** When the arena is full, the allocator compacts it, then packs closed files, whatever their age, and tries again. The `cp` of a file into a full arena succeeds this way.
* **On request.** System call 37 packs one file; `/bin/zxpack file …` uses it, `zxpack -d file …` unpacks by reading, and `zxpack` alone lists what is packed, what it saves and the memory left.
* **Rules.** Open files, directories, devices and resident programs are never packed. A file is packed only if that saves at least 8 bytes; a file that would not be smaller is flagged and left alone until it changes.

**Format.** LZ77 with a 2 KB window, greedy parsing with one step of lazy evaluation, and an adaptive binary range coder for every decision: literal or match, the 8 bits of each literal (a 255-node tree), match offsets (gamma code of offset/16 plus a 4-bit tree) and lengths (adaptive gamma). The coder is 16-bit and renormalises one bit at a time; the encoder adds carries into the bytes already written. Probabilities are 8-bit, adapt by 1/16 and are kept per previous token type. The stream has no header: the i-node keeps the real size, and its spare word holds the stream length.

**Ratios** (packed size as a share of the original): English text 54%, assembler source 28%, Z80 code 72% in 2 KB pieces — about 15% smaller than an optimally parsed LZ77 with Elias-gamma codes on text and source, and about 4% on machine code. The 1,473-byte manual page `/usr/doc/zxpack` packs to 701 bytes.

**Cost.** About 1.3 KB of kernel code, which fits because the single-user kernel dropped its permission and uid code. Encoder and decoder share the model code: `zbit` codes the bit in the carry flag when packing and returns the decoded bit when unpacking. Speed was not a goal. On a 3.5 MHz Spectrum packing 1.4 KB takes about 10 s and unpacking about 3 s. Packing encodes into a workspace block of the arena — the file's size, or half or a quarter of it when memory is short — which then becomes the file.

`tools/zxpack.py` is a bit-exact Python model: the build uses it to store `/usr/doc/zxpack` packed, and the tests check that every stream the Spectrum writes is byte-identical to the Python encoder's output.

## Kernel architecture

**Processes — preemptive, 4 slots, 50 Hz.** The ULA frame interrupt drives everything: the ROM `KEYBOARD`/`KEY-INPUT` scan, the seconds clock, sleep timers, the BREAK key, the status line and the cursor blink. Each process gets a quantum of 4 ticks (Retro UNIX `time_count = 4`). A process in user mode is preempted directly from the ISR; one in the kernel gets `runrun` set and switches at system-call return — the v1 kernel is non-preemptive inside, and so is this one. The next process is chosen round robin; with nothing runnable the scheduler HALTs until an interrupt wakes something. The ISR also counts clock ticks per process and idle ticks, which `ps` and `top` report.

**Images and the window.** As in v1, only one process is "in core" at a time — here, in a 4 KB window at F000h where the resident programs' data is linked. Each process has a SAVE block in the arena that can hold its whole image (u-area, data up to its break, 384 bytes of stack), reserved for as long as it lives, so a context switch never runs out of memory. The window is handed over lazily: an image is saved only when another resident program needs the window. `fork`, `exec` and `break` grow or shrink the SAVE block, and refuse (`Try again` / out of memory) when the arena cannot hold it. Programs from cassette (SSX1, see below) run in their own block of the arena instead, so switching to them moves only the 59-byte u-area. When such a program does not fit, the window itself is lent to the arena while it runs; resident programs wait meanwhile, and get the window back when it ends.

**System calls.** `ld a,n` / `call 6003h`, arguments in HL, DE, BC; result in HL (DE for 32-bit values); carry set with the error number in A on failure. This mirrors Retro UNIX's `int 20h` with AX/BX/CX/DX and the carry flag. All 34 v1 / Retro UNIX calls are present (0 rele … 33 ilgins, 34 sleep), plus 35 `kill`, 36 `getpid`, 37 `zxpack` (also the arena status), 38 `ticks`, 39 `screen` and 40 `ssxload`; `mount` and `umount` refuse with `EINVAL`, as there is nothing to mount.

**File system — the v1 format in the arena.** 32-byte v1 i-nodes (flags, nlinks, uid, size, the address of the file's block, ctime, mtime) in a 24-entry table; 10-byte directory entries with 8-character names (Retro UNIX v1 format); root is i-number 41; i-numbers below 41 are devices; links, `..`, `mkdir`, `rmdir` and `ls -i` work as in v1. A file or directory is one arena block, which grows with a quarter to spare when written past its end and is trimmed when the file is closed. Blocks move when the arena is compacted; only the kernel points at them, so programs never notice. Files may also be stored packed (see zxpack above).

**Pure text.** The system's programs live in the kernel image (resident text). Each `/bin` entry is a directory entry for an i-node synthesized from the program table, flagged `IFTEXT` (04000), whose contents *are* the code bytes, so `ls -l`, `cat`, `cp`, `od` and `sum` work on them. Every program starts with an 8-byte header — `JR .+8` (the Z80 twin of v1's `0405 br .+14`), text size, bss size, entry — and `exec` runs it in place.

**Programs from cassette.** `exec /dev/cassette/NAME args` runs `/etc/ldx`, which searches the tape for NAME's header (a CODE header whose second parameter is `SS`) and checks there is enough memory. It then calls `ssxload`, and the kernel takes over:
1. it reads the SSX1 file into a new block of the arena — lending it the window if it must;
2. it relocates the program;
3. it clears its bss;
4. it builds the v1 argument area and starts it.

The program gets up to about 14 KB after login.

**Memory economy.** Everything that takes arena space (1.x: swap pool space) was sized to what is really used, because every byte saved in the resident image or in a process image is a byte more for files and programs:

* the u-area holds only what the kernel reads (59 bytes, not 128: no uids, quit flag, errno word, command name or device numbers — there is one disk and nothing to mount, so device selection and mount-point crossing are gone from the kernel too);
* the user library's per-process data (222 bytes) shares one area between objects never live together — the ctime result and stat buffer, `mkdir`'s paths, and the 128-byte reader buffer, which is also the copy buffer of `cat`/`cp`/`mv`, `vi`'s yank buffer, `tar`'s staging block and `zxpack`'s read buffer;
* `/etc/glob` holds what `exec` can take (24 arguments, 158 bytes of strings) and says `Arg list too long` itself; `ls` keeps 13 bytes per name; `ps`/`top` copy only the 86 bytes of kernel globals they show;
* zxpack keeps only its 256-entry literal model in the pool; the rest of the model, its coder state and its work variables live in free low memory (the dead BASIC area, calculator memory, the gap after the tty line, unused kernel-variable slots, and the kernel stack area, of which test runs use at most 76 of 360 bytes);
* pure helpers are not duplicated: the user library calls the kernel's `div32`, `basename`, `cphlde`, `addhla`, `getw2`, `ldirz` and `ldir8`, and duplicate strings share storage;
* the 16 system calls programs make most often go through 4-byte stubs (`call sc_open` instead of `ld a,_open` / `call SYS`), identical instruction tails end in a jump to one copy (found and applied mechanically, byte-exact, never across a label), and short repeated sequences became small kernel helpers.

Compared with release 1.3 every process image is at least 147 bytes smaller (glob 1,578, ls 381, ps/top 319, cat/cp/mv about 280, vi/tar/zxpack 275) and the pool is 3,407 bytes larger: beside init and the shell, 6,202 bytes are left for two more processes instead of 2,501. This version also drops programs that have no use on this machine: `pr` (pages for a line printer), `mount`/`umount` (nothing can be mounted), `/bin/kill` (the shell's built-in `kill` always ran instead), `tty` (one terminal), `who` and its `/tmp/utmp` (one user), and `ed` (`vi` is the editor).

**Devices.** `/dev/tty` (ROM keyboard and the 64-column screen below, canonical line discipline with echo, `stty` raw/echo; in raw mode the cursor keys are delivered, and output understands the Spectrum's `AT row,col` and `INVERSE n` control codes, range-checked — that is how `vi` addresses the screen), `/dev/mem`, `/dev/tap` and `/dev/cassette` (the same device: one `write` = one cassette block via ROM `SA-BYTES`, one `read` = `LD-BYTES`; a transfer of exactly 17 bytes is a standard Spectrum header block, anything else a data block; BREAK aborts with an error instead of crashing to BASIC).

### Routine map — Retro UNIX 8086 v1 → Z80

| Retro UNIX module | Routines | Z80 implementation |
|---|---|---|
| UNIX.ASM | constants, `user`/`proc`/`inode`/`systm` structures, epoch conversion | `const.inc`, `kvars.inc`, `settime`, `div32` |
| U0 | `kernel_init`, `panic`, `kb_int`, `ctrlbrk`, COM ports | `boot`, `panic`, `rom_error` (RST 8 via ERR_SP); keyboard through ROM KEYBOARD/KEY-INPUT in `isr`; BREAK via ROM BREAK-KEY → `ttintr`; no serial ports |
| U1 | `sysent`, `sysret`, `error`, `sysexit`, `syswait`, `sysfork`, `sysread`, `syswrite`, `sysopen`, `syscreat`, `sysclose`, `sysmkdir`, `sysstty`, `sysgtty`, `sysmdate`, `sysemt`, `sysilgins` | `sysent`, `sysok`/`syserr`/`sysx`, `doexit`, `syswait`, `sysfork`+`forkret`, `rw`, `sysopen`, `syscreat`, `sysclose`, `sysmkdir`, `sysstty`, `sysgtty`, `sysmdate` |
| U2 | `syslink`, `sysunlink`, `sysexec`, `sysstat`/`sysfstat`, `fclose`, `getf`, `namei`, `syschdir`, `syschmod`, `syschown`, `systime`, `sysstime`, `sysbreak`, `maknod`, `sysseek`/`systell`, `sysintr`/`sysquit`, `syssetuid`/`sysgetuid`, `anyi` | same names, except: `chown` and `setuid` succeed and do nothing, `getuid` returns 0, `anyi` became `isopen`; `kexec` builds the v1 argument layout (argc, argv…, strings at the top of core); one root, nothing to mount |
| U3 | `tswap`, `swap`, `wswap`, `rswap`, `idle` | `swtch` (round robin, HALT idle), `swapout` (u-area), `swapin`, `wsave`/`wload` (the window image to and from the SAVE block), `savefit`; the arena allocator `aalloc`/`afree`/`acompact` (`arena.asm`), window lending `lend`/`unlend` |
| U4 | `clock`, `sleep`, `wakeup`, `isintr` | `isr`, `tick1s`, `ticksleep`, `ksleep`, `kwakeup`/`wakeslot`, `sigck` |
| U5 | `mget`, `alloc`, `free`, `iget`, `icalc`, `access`, `setimod`, `itrunc`, `imap` | one arena block per file instead of blocks (`writei` grows it), `iget` (table, devices, resident text), no `access`/`owner` (single user), `setmtim`, `itrunc`, `ialloc`/`ifree` |
| U6 | `readi`, `writei`, `rtty`, `wtty`, `rmem`, `wmem`, `dskr`, `dskw`, `passc`, `cpass` | `readi`, `writei`, `ttread`/`ttgetc`, `ttwrite`/`kputc` (64-column console), `memrd`/`memwr`; passc/cpass become block moves |
| U7 | `sysmount`, `sysumount`, `iopen`, `iclose`, `otty`, `ctty` | none for mount/umount (nothing to mount: the calls refuse), `fopen`, `fclosea` (trims the file's block), `fpdup` |
| U8 | `bread`, `bwrite`, `bufaloc`, `dskrd`, `dskwr`, `poke` | not needed: files are blocks of memory |
| U9 | `getc`/`putc`, video, `beep`, INT 16h/09h keyboard, `syssleep` | `kputc`/`glyph`/`tscrl`/`kcls` (4 × 8 font console), `cxor`/`cblnk` (cursor), ROM BEEPER, KEYBOARD, KEY-INPUT; `stdraw` (status line); `syssleep` |

**ROM routines used:** KEYBOARD 02BFh, KEY-INPUT 10A8h, BREAK-KEY 1F54h, BEEPER 03B5h, SA-BYTES 04C2h, LD-BYTES 0556h, the error restart RST 8 (trapped through ERR_SP), the FFh filler at 3900h–3A00h and byte 0000h for the IM 2 vector, and LOAD for booting.

## User-land

All programs are new Z80 code; the PDP-11 originals (quoted in Retro UNIX's comments) defined their behaviour and messages.

| Group | Programs |
|---|---|
| Retro UNIX 8086 v1 set | `/etc/init`, `/etc/getty`, `/etc/glob`, `login`, `sh`, `ls`, `cat`, `cls`, `mkdir`, `rmdir`, `cp`, `rm`, `chmod`, `pwd`, `ln`, `mv`, `date`, `df` |
| Further UNIX v1 commands | `cmp`, `du`, `od`, `stat`, `sum`, `tap`, `wc` |
| Later UNIX | `vi`, `ps`, `top`, `tar` |
| This port | `zxpack` |
| Conveniences | `echo`, `sleep` (and `kill` built into the shell) |
| Retro UNIX demos | `hello`, `beep`, `clock`, `forktest` |

**sh** is the v1 shell: `;` and `&` separators, `<` `>` `>>` redirection, `"…"` `'…'` quoting, `*` `?` `[…]` through `/etc/glob`, `$0`–`$9` in command files, built-ins `chdir`/`cd` and `login`. Messages follow Retro UNIX: `Try again`, `Arg count`, `Bad directory`, `Input file`, `Output file`. **tar** and **tap** archive files on cassette (below).

**vi** is a small visual editor for the 64 × 23 text area: 22 text rows and a status line, with horizontal scrolling for lines longer than 64 characters.

* **Moving:** `h j k l` or the cursor keys, `0`, `$`, `[n]G`, `/text`.
* **Editing:** `x`, `dd`, `p`, `r`, `J`, and `i a A o O` to insert.
* **Saving and quitting:** `:w [file]`, `:q`, `:q!`, `:wq`, `:n` (go to line n), `ZZ`.

In insert mode ENTER splits the line, DELETE erases, and EDIT (CAPS SHIFT+1) is Escape. Its buffer (about 2.5 KB) grows with `break`.

**ps** and **top** read the kernel's process table through `/dev/mem`, as early UNIX `ps` read core. `ps` lists PID, PPID, state, CPU time and command; `top` refreshes every 2 seconds with per-process %CPU, data size and idle percentage until you press BREAK.

## Adaptations

* **4 process slots.** init, the shell and two more processes — a command plus a background job, or a program and its child. When all four are busy, `fork` answers with v1's `Try again`, and it reuses the slot of an unwaited zombie child.
* **Shell built-ins:** `chdir`/`cd`, `login`, plus `kill pid`, `exec cmd`, and `sh file [args]`, which runs a command file inside the current shell.
* **No second disk.** `/dev/rd1` was dropped to make room for `vi`, `ps` and `top`, and with it `mount` and `umount`: there is nothing to mount.
* **One user, one terminal.** There is no `who`, `tty` or `/tmp/utmp`; `ps` and the status line show what runs.

**Other differences:** `ls -l` prints mode, links, size, date and name (no owner — there is only one user), and `od` shows 8 words a line as in v1. There is no printer, since its buffer holds the kernel. The clock starts at Wed Nov 3 1971 (the v1 manual date); set it with `date mmddhhmm[yy]`.

## C programs

```
python3 sdk/lib/build.py                    # the C runtime
sdk/bin/rcc game.c -o game.ssx              # compile: native Z80, or SSB1 bytecode if it is big
sdk/bin/rvm game.ssx --png game.png         # try it on the host
sdk/bin/rtap -o game.tzx game.ssx           # its cassette record
```

On runix:
1. Type `/dev/cassette/game [args]` and play the tape.
2. The program owns the screen while it runs; when it exits, the picture stays and the shell carries on below it.

The language is C48 (the ZX-UX C48 SDK's C subset): `int`/`char`/`short`/`unsigned`, five-byte Spectrum floats computed by the ROM, pointers, arrays, recursion. The library covers:
* the 64-column console with colours, plot/draw/circle and UDGs;
* raw keys, ticks, sleep and beep;
* strings, `malloc`;
* files.

`tools/mktapes.py` compiles the C48 SDK's 56 corpus programs and writes them to tapes:
* `build/c48-games.tzx`, `-demos`, `-apps`, `-examples`;
* `build/runixz80-c48.tzx`: the system followed by every program.

`chess` and `write48` are built in bytecode (SSB1) and borrow the window to run.

**A program in the background.** Start a cassette program with `&` (`/dev/cassette/hanoi &`) and the shell stays usable below the picture: as soon as you type, the console takes text rows 21–22, the status line comes back on row 23, and the program draws only rows 0–20. Commands run as usual; their output scrolls through the two console rows.

**Two programs at once.** `hanoi` and `queens8` share the screen, each drawing one half. `build/c48-multitask.tzx` holds both, built small enough to fit together (bytecode, measured stacks, and a 16-slot UDG bank for hanoi: `rcc --bytecode --stack 400 --udgs 16`, `rcc --bytecode --stack 448`):
1. Type `/dev/cassette/hanoi &` and play the tape. It stops by itself after hanoi has loaded.
2. Once hanoi is drawing, press ENTER for a prompt below the picture, type `/dev/cassette/queens8 &` and play the tape again.

Together they need 10,396 bytes (5,188 + 5,208; 13,381 in 2.1), which the arena holds beside the file system, so neither borrows the window and the shell keeps running below the pictures. With init, sh, hanoi and queens8, all four process slots are taken and only about 150 bytes are free, so the shell's built-ins work (`cd`, `kill pid`) but a command says "Try again" until one of the programs ends. The details are in `sdk/README.md` and `docs/SPEC-SDK-R2.md`.

## Building and testing

```
python3 tools/build.py          # assemble (sjasmplus), build the i-node table and arena, write build/runixz80.tzx + .tap
tools/t.sh SCRIPT               # build, load the TZX through the ROM loader, run a session
python3 tools/zxrun.py build/test.z80 SCRIPT
```

`tools/zxrun.py` is a headless 48K harness built on SkoolKit's C Z80 simulator. It types through the keyboard half-row ports, emulates the cassette in both directions (it decodes what `SA-BYTES` writes and plays it back for `LD-BYTES`), reads the 64-column screen back as text through the 4 × 8 font, and writes PNG screenshots. Test sessions covered:
* boot, login, logout and getty respawn;
* every program, redirection and globbing;
* large (indirect-block) files, disk full and recovery;
* BREAK and EOF handling, background jobs and `kill`;
* 4 processes swapping through the pool, preemptive `forktest`;
* `ps`, `top` and `vi` editing sessions;
* `tar` round trips through the emulated cassette: directories, packed files, labelled archives, extracting a selection, replacing files, recreating directories;
* zxpack: unpack on read, idle repacking and its abort on a keypress, packing under memory pressure, incompressible files, large files;
* programs from cassette: arguments, searching past other programs, window lending, a background job waiting through a lend, a program too big to load.

`tests/suite.py` is the regression suite (20 sessions, each from a fresh tape-loaded snapshot): `python3 tests/suite.py [-k name,...] [-v]`. `tests/ssxrun.py` runs every C48 corpus program on runix from cassette and saves a screenshot of each; `sdk/tests/oracle.py` checks the compiler and VM against the C48 SDK reference.

## Files

```
src/const.inc   memory map, fs layout, syscall numbers, ROM entry points
src/kvars.inc   kernel globals (printer buffer) and the u-area
src/unix.asm    boot, ISR/clock, scheduler/swap, system call dispatch, process calls, exec
src/fs.asm      namei, iget, bmap, alloc/free, readi/writei, itrunc, open file table, fs calls
src/dev.asm     tty (ROM keyboard/screen, AT/INVERSE pass-through), mem, tape, stty/gtty
src/arena.asm   the arena allocator, compaction, window lending
src/cext.asm    C support calls: ticks, screen
src/t_ldx.asm   /etc/ldx, the cassette program loader
src/ulib.asm    user library (args, output, numbers, ctime, sort, buffered input, directory entries)
src/t_sys.asm   init getty login sh glob
src/t_file.asm  cat cp mv ln rm rmdir mkdir chmod ls pwd df
src/t_misc.asm  date stat wc od cmp sum echo sleep cls demos
src/t_tap.asm   du
src/t_tar.asm   tar, tap (the cassette archiver)
src/tar.doc     /usr/doc/tar (stored packed)
src/t_proc.asm  ps top
src/t_vi.asm    vi
src/zx.asm      zxpack: range coder, LZ77 parser, pack/unpack, idle and pressure packing
src/t_zx.asm    the zxpack command
src/zxpack.doc  /usr/doc/zxpack (stored packed)
src/font4x8.bin console font (SANYALnet Labs 4x8), src/font4x8.LICENSE its license
src/programs.txt  /bin and /etc entries (path, label, set-uid)
tools/build.py  assembler driver, i-node table and arena image, BASIC loader, TZX/TAP writer
tools/zxpack.py bit-exact reference codec
tools/mktapes.py  the C48 corpus compiled and written to cassette tapes
sdk/            the runix SDK: rcc, ras, rld, rtap, rvm, runtime library (sdk/README.md)
tests/ssxrun.py the C48 corpus on runix;  tests/c/  C test programs for the suite
docs/           SPEC-ELASTIC-R2.md, SPEC-SDK-R2.md (and their R1 designs)
tools/zxrun.py  headless test harness;  tools/t.sh  build + test
tests/suite.py  regression suite
```

Retro UNIX 8086 v1 is © Erdogan Tan (singlix.com/runix); UNIX v1 by Ken Thompson and Dennis Ritchie. This port reimplements their design for the Z80 and contains none of their code.

The console font `src/font4x8.bin` ("SANYALnet-Labs-4x8-font-FINAL") comes from the ZX-UX c48 SDK. Based on original work by Supratim Sanyal of SANYALnet Labs. It is used under the SANYALnet Labs Non-Commercial License, reproduced in `src/font4x8.LICENSE`; that license (non-commercial use, attribution required) therefore applies to builds that include the font.

# ZX-UX: Memory and File Formats, R1

This file describes the first memory design. It is kept so the changes are
clear. Some ideas in R1 were not built. Read `SPEC-ELASTIC-R2.md` for the
later system, and check the source for the current behavior.

R1 describes how processes and files can share one area of RAM. It also
defines the SSX1 program, SSO1 object, SSA1 library, and tape formats.

## 1. Design choices

| # | Decision | Consequence |
|---|---|---|
| D1 | Files live in an elastic arena with real v1 directories | i-nodes, directory objects, `ln`, `mkdir`, `rmdir` and `ls -i` keep working; no blocks, no fixed disk |
| D2 | `fork` is kept and implemented by *twin swapping* | `sh`, `init`, `&` and `forktest` keep v1 semantics |
| D3 | Formats are named SSX1, SSO1, SSA1, SST1 and SSZ1 | §6–§10 |
| D4 | The 35 system commands stay resident (pure text in the kernel image) | Their data stays linked at the fixed core window (§3.3), so the window and its swapping stay |
| — | Preemptive multitasking, 4 process slots, single user, no permissions | unchanged from 1.x |
| — | Cassette is the persistent store; programs from the C toolchain are loaded from cassette | §9 |

## 2. Goal and success measure

The goal is to run the **biggest possible user program** produced by the offline C compiler, without
giving up a recognisable v1 UNIX.

Success measure: the largest SSX1 program that loads from cassette and runs beside `init` and an
interactive `sh` with `/tmp` empty. The estimate for this design is about 14 KB (§3.5). In release
1.4 the corresponding limit was about 4 KB of core, and the 8 KB RAM disk could hold only about 3 KB
of binary.

## 3. Memory model

### 3.1 Memory map

    0000-3FFF  ROM
    4000-5AFF  display file and attributes
    5B00-5FFF  kernel globals, system variables, kernel stack, tty line,
               exec arguments, zxpack low-memory state (as in 1.x)
    6000-....  KERNEL          resident kernel (at most 8192 bytes)
    ....-....  FONT            console font (384 bytes)
    ....-A0    RESIDENT TEXT   user library + resident commands (pure text)
    A0  -A1    ARENA           elastic memory: files, process images, saves
    A1  -EFFF  ZMODEL          zxpack literal model (256 bytes, fixed)
    F000-FFF3  WINDOW          core window for resident-text processes
    FFF4-FFFF  IM 2 trampoline

`A0` is the first byte after the resident text and is computed at build time. `A1` = `WINDOW` − 256.
With today's code sizes the arena would be about 16.5 KB (AE74h–EEFFh). the kernel changes in this
rewrite will move it by a few hundred bytes.

`WINDOW` is a build constant (default F000h, 4084 bytes). It can be made smaller later if the
resident commands' data needs allow it. each byte removed from the window is a byte more in the
arena.

### 3.2 Arena allocator

The arena is one region managed by one allocator. Every allocation is a **block**:

    +0  u16 size      total block size in bytes, including this header; even
    +2  u8  owner     who points at this block (see below); 0 = free
    +3  u8  kind      FILE, DIR, SAVE, TWIN, IMAGE, KERN

- Payload starts at +4. Blocks are even-aligned, and the smallest block is 4 bytes.
- **Owner** is an i-node index for FILE and DIR blocks, or a process slot for the others. Kernel-owned blocks use 255.
- Free blocks are coalesced on free.

**Placement:**
- **Movable** blocks (FILE, DIR, SAVE, TWIN) are allocated first-fit **from the bottom**.
- **Fixed** blocks (IMAGE — an SSX1 program — and KERN) are allocated **from the top**, best fit.
- Fixed blocks hold absolute addresses after relocation and never move.

**Compaction:**
- When an allocation fails, the allocator compacts once and retries before reporting `ENOMEM`.
- Compaction slides every movable block down over free space and rewrites its single owner pointer. That is the i-node's extent pointer, or the process slot's save or twin pointer.
- Only the kernel holds pointers to movable blocks; user programs reach files through `read`/`write`, so compaction is invisible to them.

**Pressure packing:** before reporting `ENOMEM`, the allocator may also pack one closed FILE object with zxpack (§10). The 1.x rules still apply: never open files or directories, and only when packing saves space.

### 3.3 The core window

Resident commands are linked with their library data and BSS at fixed addresses in `WINDOW` (`UDATA`
and up), so only one process at a time can have its data there.

- A process whose program is resident text (or an SSX1 image built with the WINDOW flag, §6.2) is a **window process**. Its image is:
  - the u-area and data up to its break, at `WINDOW`
  - its stack, at the top of the window
  - the argument area, just below `FFF4h`
- The kernel tracks a **window owner**: the process whose image is in the window. When a different window process is scheduled, the owner's image is copied into its SAVE block and the incoming process's SAVE block is copied into the window. This is 1.x swapping with the pool replaced by arena blocks.
- Window ownership is **lazy**. Switching to an SSX1 process (§3.4) leaves the window untouched, so alternating between a window process and an SSX1 process copies nothing.

**Reservation rule (no swap failures):**
- Every window process owns a SAVE block for as long as it exists, sized to its current extent: break − `WINDOW` + its stack reserve. It owns this even while it is the window owner.
- A context switch therefore never allocates. `brk`, `exec` and `fork` grow or create SAVE blocks first and fail with `ENOMEM` if they can't.
- This replaces 1.x's `rescheck`.

### 3.4 SSX1 processes

An SSX1 program loaded from cassette (or from a file) gets one **IMAGE** block holding everything it
uses:

    IMAGE block payload:
      image (text + data)  relocated to the block's address
      bss                  zeroed
      heap                 grows up from the end of bss (brk)
      ...
      stack                grows down from the top of the block
      arguments            argc, argv, strings at the very top

- **Heap growth:** `brk` stays inside the IMAGE block, up to the stack reserve. The block is sized when the program is loaded, from the header's stack reserve plus an optional heap reserve (§6.2).
- **Context switch:** the program's data and stack never move, so switching to or from an SSX1 process saves and restores only the 59-byte u-area. The u-area lives in a small SAVE block owned by the slot.
- **U-area rule:** the kernel reaches the u-area at a fixed address, so the window's first `UASZ` bytes always hold the *running* process's u-area. Switching from window owner A to SSX1 process B saves A's u-area into A's SAVE block and loads B's. Switching back restores A's u-area; A's data beyond the u-area was never disturbed.

### 3.5 Biggest program estimate

Arena ≈ 16,524 bytes (today's boundaries). The two resident window processes that are always present
have actual images of about:
- `init`: u-area + 222-byte library arena + small stack ≈ 0.35 KB
- `sh`: ≈ 1.3 KB

These are actual extents, not 1.x's worst-case `STKRES` accounting. Directories `/`, `/bin` (350
bytes), `/dev`, `/etc`, `/tmp` and `/usr` take about 0.6 KB.

**Largest SSX1 program ≈ 16.5 − 0.35 − 1.3 − 0.6 − 0.6 (`/etc/motd`, i-node table if placed in the arena, slack) ≈ 13.5–14 KB**, counting image + bss + heap + stack. A 2 KB window instead of 4 KB would add about 2 KB.

### 3.6 Twin swapping (`fork`)

- **Fork of a window process:** the child gets its own SAVE block, a copy of the parent's current window image, and is a normal window process. Behaviour is identical to 1.x.
- **Fork of an SSX1 process:** the child must run at the parent's addresses. The two become **twins** sharing the parent's IMAGE block:
  - The non-running twin's copy of the IMAGE block's contents is kept in a TWIN block (movable, same size).
  - Scheduling the other twin exchanges the IMAGE block's contents with the TWIN block, by a byte exchange in place, so no third buffer is needed.
  - `fork` fails with `ENOMEM` if the TWIN block can't be allocated.
- **Leaving the twin state:**
  - When either twin calls `exec`, it gets a fresh IMAGE (or becomes a window process) and the TWIN block is freed.
  - When either exits, the survivor keeps the IMAGE block, and the TWIN block is freed after the IMAGE contents are restored to the survivor if necessary.
- The common `fork`→`exec` pattern therefore costs one image copy for a moment. A real `fork` (`forktest`, a background subshell) works with no restrictions.

### 3.7 Fixed kernel allocations

KERN blocks hold kernel data that has no fixed home: the i-node table (§4.2), if it doesn't fit in
low memory, and transient loader buffers. They are allocated from the top and freed as soon as
possible.

## 4. Elastic v1 file system

### 4.1 Model

v1 semantics are kept:
- i-numbers, link counts, directories that are files of 10-byte entries (2-byte i-number + 8-character name), `.` and `..`, mode bits, mtime and ctime
- devices as i-numbers below 41

Storage is elastic: each file or directory is one FILE or DIR block whose payload is the file's
bytes, exactly as long as the file plus allocation rounding. There are no data blocks, indirect
blocks, free-block bitmaps or superblock.

### 4.2 I-node table

A fixed kernel table of **NINODE = 32** records of 16 bytes (512 bytes):

    +0   u16 flags     IALLOC IFDIR IFTEXT IFPACK + v1 mode bits (as 1.x)
    +2   u8  nlinks
    +3   u8  reserved
    +4   u16 size      logical length
    +6   u16 stored    payload length in the block (less than size if packed)
    +8   u16 extent    address of the FILE/DIR block payload, 0 if empty
    +10  u32 mtime
    +14  u16 ctime-days  creation date in days since 1970 (time of day dropped)

- **I-number ranges:**
  - 1–40: devices (synthesized i-nodes, as in 1.x)
  - 41–72: table entries
  - 128–255: resident programs
- A resident program's i-node is synthesized from the build's program table: IFTEXT, size = text size, extent = text address. Like 1.x devices, it takes no table entry.
- `/bin` is an ordinary directory whose entries point at these synthesized i-numbers, so `ls -l /bin`, `cat /bin/ls` and `cp /bin/ls x` behave as in 1.x. Users may add entries (`ln`, or SSX1 files) to `/bin`.

**Placement:** the table's 512 bytes are a KERN block allocated at boot. If low memory can be found for it, it moves there in a later revision.

### 4.3 Operations

| Operation | Behaviour |
|---|---|
| `read` | copies from the extent; a packed file is unpacked first into a new block, the packed block is then freed (atomic: on `ENOMEM` the file stays packed and the read fails) |
| `write` | if the write fits the block's capacity, copies in place; otherwise reallocates (allocate new size rounded up to 32 bytes, copy, free old); on `ENOMEM` nothing changes and the write returns `ENOSPC` with the bytes written so far |
| `creat` on an existing file | truncates: frees the block, extent = 0 |
| `unlink` | drops a link; at 0 links and no open descriptor, frees the block and the i-node (1.x rules for open files kept) |
| `mkdir` / `link` / `rmdir` | as 1.x, on directory objects |
| `stat` | 1.x layout; the block count is replaced by stored size (`du`, `ls -s` report stored bytes / 128 rounded up, to keep their output familiar) |
| raw `/dev/rd0` | **removed**: there is no disk device; `tar` and `zxpack` use `stat` and normal I/O instead |

### 4.4 What replaces the boot RAM disk image

At boot the kernel builds the root directory tree from a small **boot file set** carried in the
kernel tape blocks:
- `/`, `/bin` (with the resident program entries), `/dev`, `/etc`, `/etc/motd`, `/tmp`, `/usr`, `/usr/doc`

The two manual pages become optional SST1 files on the system tape, loaded on demand.

## 5. Process model summary

| | Window process | SSX1 process |
|---|---|---|
| Program text | resident (shared, pure) | in its IMAGE block |
| Data, bss, heap, stack | in `WINDOW` | in its IMAGE block |
| Saved on switch | whole image (lazy: only when another window process takes the window) | u-area only |
| Memory held when not running | SAVE block (image size) | IMAGE block + 59-byte SAVE |
| `fork` child | window process with its own SAVE | twin (§3.6) |

Scheduling, quantum, sleep and wakeup, signals and the status line are unchanged from 1.x. `NPROC`
stays 4.

## 6. SSX1 — executable

### 6.1 Layout

    header (20 bytes)
    image (text + initialised data), linked at address 0
    relocation stream

### 6.2 Header

| Offset | Size | Field |
|---|---|---|
| 0 | 4 | magic `'S' 'S' 'X' '1'` |
| 4 | 1 | flags (below) |
| 5 | 1 | header size = 20 |
| 6 | 2 | image size |
| 8 | 2 | bss size |
| 10 | 2 | stack reserve — includes 160 bytes for kernel and interrupt use on the user stack |
| 12 | 2 | heap reserve — extra bytes above bss available to `brk` |
| 14 | 2 | entry offset within the image |
| 16 | 2 | relocation count |
| 18 | 2 | checksum: Fletcher-16 over header bytes 0–17, the image and the relocation stream |

All fields are little-endian. **Flags:**
- **bit 0 `WINDOW`:** not relocatable; image linked at `UDATA` (or at a stated address ≥ `UDATA`); loaded into the window as a window process. The relocation count must be 0.
- **bit 1 `PACKED`:** the image and relocation stream that follow are one SSZ1 stream (§10); the header itself is never packed.
- **bits 2–7:** must be 0 in revision 1.

A loader rejects a header whose magic, header size, flags or checksum is wrong, and any size
combination that overflows 16 bits.

### 6.3 Relocation stream

Relocations mark 16-bit little-endian words in the image that hold addresses relative to image start
(link address 0). The loader adds the load address to each.

The stream encodes positions as increasing offsets, so the loader can patch while the image streams
in from tape:

| Byte(s) | Meaning |
|---|---|
| `01`–`FF` | advance the position by this many bytes and relocate the word there |
| `00 lo hi` | set the position to the 16-bit offset `hi:lo` (must be greater than the current position) and relocate the word there |

- The position starts at 0 before the first entry; the first entry is therefore its own offset if it is 1–255, or an escape.
- Exactly `relocation count` relocations follow, and every relocated word must lie entirely inside the image.
- Typical cost is about 1.1 bytes per relocation.

### 6.4 Loading a program safely

1. Read and check the header.
2. Allocate the IMAGE block: image + bss + heap reserve + stack reserve + argument area. If this fails, `exec` returns `ENOMEM` to the caller.
3. Stream the image into the block, applying relocations as the stream is read.
4. Verify the checksum. On a checksum or tape error (including BREAK), free the block and return `EIO` to the caller: the caller's image was never touched, so `exec` from cassette is atomic.
5. Only now discard the caller's old image (its SAVE block or IMAGE block), zero the bss, and build the arguments at the top of the block in the v1 layout (`SP` → argc, argv[0..n−1], 0, strings).
6. Jump to the entry point with interrupts enabled.

Because the old and new images coexist until step 5, the biggest program is loaded from a small
caller (normally a child of `sh`, whose window image is small). the figure in §3.5 already assumes
that.

The system call interface is unchanged (`ld a,n` / `call 6003h`). The C calling convention is
defined by the compiler documents, not here.

## 7. SSO1 — relocatable object (host side)

The compiler, assembler and linker run offline, so SSO1 is designed for the host and is never read
on the Spectrum in revision 1. It is defined here so all host tools share one format.

    header:   'S' 'S' 'O' '1', u8 version = 1, u8 flags = 0,
              u16 section count, u16 symbol count, u32 string table size
    sections: for each: u8 kind (1 text, 2 data, 3 bss), u8 align (power of 2),
              u16 size, u16 relocation count, then size bytes (not for bss),
              then relocations
    symbols:  for each: u32 name offset (string table), u8 section (0 = undefined,
              255 = absolute), u8 binding (0 local, 1 global), u16 value
    strings:  NUL-terminated names

**Relocation record (6 bytes):**

    u16 offset in section, u8 type, u8 reserved, u16 target

- **Types:**
  - 1 `ABS16_SEC`: target = section index
  - 2 `ABS16_SYM`: target = symbol index
  - 3 `HI8_SYM` and 4 `LO8_SYM`, reserved for the assembler's `high()`/`low()`; they can't appear in an SSX1 image, so the linker must resolve them
- The linker resolves every symbol, lays out text, then data, then bss, and emits an SSX1 image with ABS16 relocations only.

## 8. SSA1 — object archive (host side)

    header:  'S' 'S' 'A' '1', u16 member count, u16 reserved
    index:   for each member: u32 offset, u32 size, NUL-terminated name
    members: SSO1 objects

The linker scans an archive's members for unresolved symbols, as `ld` does with libraries. Revision
1 keeps the index unsorted.

## 9. SST1 — cassette record

One file on cassette. `tar` archives are sequences of SST1 records between archive begin and end
records. Running a program from tape means finding an SST1 record whose payload is SSX1 and
streaming it into an IMAGE block.

**Spectrum header block (17 bytes, flag 00):**
- type 3 (CODE)
- name = the file's base name, up to 10 characters, space padded
- length = record payload length
- param1 = record kind:
  - `'F'` file
  - `'D'` directory
  - `'A'` archive begin
  - `'E'` archive end
  - `'X'` executable run straight from tape
- param2 = `'S','S'`

**Payload (data blocks of up to 512 bytes, flag FF; a 17-byte block is sent as 18):**

    +0   'S' 'S' 'T' '1'
    +4   u8  flags       bit 0 PACKED (payload is SSZ1), bit 1 DIRECTORY
    +5   u8  mode        v1 mode bits
    +6   u16 logical size
    +8   u16 stored size
    +10  u32 mtime
    +14  path, NUL terminated (full path as archived)
    ...  stored bytes

Archive begin and end records carry the archive label as their name and no payload.

- **Compatibility:** 1.x `tar` tapes (preamble without the `SST1` magic) can still be read. The reader recognises the old preamble by the missing magic. New tapes are always SST1.
- **Running from tape:** `exec /dev/cassette/name [args]` searches forward for a record named `name` with kind `'X'` (or an `'F'` record whose payload starts with `SSX1`) and loads it as in §6.4.

## 10. SSZ1 — packed stream

The zxpack codec of 1.x, unchanged and bit-exact with `tools/zxpack.py`:
- LZ77 with a 2 KB window
- adaptive binary range coder
- 342 adaptive probabilities

A packed **file** keeps its sizes in its i-node and stores the bare stream. A packed stream that
stands alone (an SSX1 image body, an SST1 payload) is preceded by:

    'S' 'S' 'Z' '1', u16 logical size, u16 stream size

**Decoding sinks:**
- to a new arena block (unpacking a file)
- straight into an IMAGE block while applying relocations (packed SSX1)
- to the tape writer (archiving a packed file packed)

## 11. Kernel changes from 1.x

| Area | 1.x | 2.x |
|---|---|---|
| File storage | 8 KB block RAM disk | arena FILE/DIR blocks |
| `fs.asm` | blocks, `bmap`, `alloc`/`free`, `itrunc`, bitmaps | extents, allocator, compaction; namei and directory code kept |
| Swap pool | fixed region, `rescheck` | SAVE/TWIN blocks, reservation rule |
| `exec` | resident text or fixed load at `UDATA` | resident text, SSX1 relocating loader, from file or cassette |
| zxpack | packs disk blocks | packs FILE blocks, decodes into any sink |
| `/dev/rd0` | raw disk | removed |
| `tar` | 1.x preamble | SST1, reads 1.x tapes |

## 12. Implementation phases

| Phase | Content | Done when |
|---|---|---|
| 1 | Arena allocator with compaction; elastic v1 file system; boot file set; `/dev/rd0` removed; `tar`, `zxpack`, `df`, `du` adapted | the 1.x regression suite passes with files in the arena |
| 2 | Window SAVE blocks replace the swap pool (reservation rule) | suite passes; `pool_capacity`-style tests pass with arena saves |
| 3 | SSX1 loader (file and cassette), IMAGE blocks, u-area-only switches, twin swapping | hand-assembled SSX1 test programs run, fork, exec and exit |
| 4 | Host toolchain: SSO1/SSA1/SSX1 writers, linker, assembler output | linked programs load and run on ZX-UX |
| 5 | C compiler backend and runtime | compiled programs run from cassette |
| 6 | Measure and tune: window size, NINODE, reserves | biggest-program figure measured |

## 13. Open questions for later revisions

- Whether some resident commands should become SSX1 programs on the system tape (deferred: they stay resident for now).
- `WINDOW` size: 4 KB keeps 1.x behaviour for `vi`'s buffer; smaller frees arena.
- Whether the i-node table can live in low memory.
- `HI8`/`LO8` relocations in SSX1, if a need appears.

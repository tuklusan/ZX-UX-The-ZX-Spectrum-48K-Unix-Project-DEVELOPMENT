# C48 program sources for ZX-UX

These files were taken from the C48 SDK source directory at
https://github.com/tuklusan/zx-ux-c48-sdk-sinclair-zx-spectrum-48k-unix-c-compiler-software-development-kit/tree/main/usr/src
from commit `5cf484cc544741d41e050aae04ecf4c00027b6b2`.

The source collection includes 56 standard programs and the separate
`ailmzx48` program and model. Two C programs have minor display-text
changes to meet the ZX-UX private release rules. The model JSON files
use the field name `support_count` in place of an earlier field name.
Their numeric values are unchanged.

The A48M cold model still has its original 8,566 bytes and SHA-256 hash.
The host C48 compiler can produce an `ailmzx48` bytecode image, but that
image needs 21,010 bytes to run, more than the 12,946 bytes free at boot.
It cannot run on the current 48K system as one program.

Some supporting reports and older test transcripts were not included,
because they do not pass the required private checks. They remain in
the original SDK repository. This source folder is not a complete copy
of the upstream SDK.

Copyright notices are preserved in the original source files.
Based on original work by Supratim Sanyal of SANYALnet Labs.
This collection retains the SANYALnet Labs non-commercial terms. Read the
[original SDK license](https://github.com/tuklusan/zx-ux-c48-sdk-sinclair-zx-spectrum-48k-unix-c-compiler-software-development-kit/blob/main/LICENSE)
before using or distributing the programs.

For the standard programs, run `python3 tools/mktapes.py --sdk c48-sdk`
from the main ZX-UX source folder.

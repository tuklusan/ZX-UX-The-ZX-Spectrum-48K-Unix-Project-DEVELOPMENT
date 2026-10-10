<!--
ZX-UX Unix ZX Spectrum 48K SDK © 2026 SANYALnet Labs supratim-sanyal.blogspot.com

SANYALnet Labs Non-Commercial License, attribution to SANYALnet Labs required, see LICENSE for more information
-->

# ailmzx48 language model

The C48 SDK model stores a cold A48M v2 stream in `cold-seed.bin`.
The adjacent JSON file records its length, checksum, and interface ID.
The current model and saved iterations keep their original numeric
values. The old trigram counter field is now called `support_count`.
This is a JSON field-name change, not a change to the stored weights.

The cold stream is limited to 65,535 bytes. Readers request at most
64 bytes at a time, and each record is at most 192 bytes long.
The SDK program uses C48B1 bytecode. It is not a native Z80 image.
It is too large for the current on-device compiler as one C unit.
Do not claim native build success until it is split and tested.

SANYALnet Labs

OUTLANDER — The Spectrum Show collection

We kept the original Outlander.z80 snapshot and the collection's Outlander.tzx without changes. The existing Fuse 48K replay uses the snapshot and sends A, P, S and O after skipping the instructions. We ran the same input sequence again in genuine Fuse SDL and checked two distinct live game screens. Scrolling scenery may also change without a key press. No hit, exact player movement or finished round was proved.

We checked the tokenized TZX with the ZX-UX ROM-style line formatter. It contains 149 physical BASIC records: four records numbered 0, followed by 145 records in increasing line-number order. All 149 individual records can be formatted, including the four opening REM lines. The strict TZX-to-BASIC tool rejects the repeated line number 0. A standard, uniquely numbered LLIST file cannot be verified from this tape without changing its source records, so no separate .bas file was published. We did not rewrite the original media or pretend that the four duplicate records are an ordinary saved BASIC listing.

The source instructions give A left, S right, P up, L down and O fire. See KEYS-AND-TIMING.txt and REPLAY.sh for the recorded short run. The two existing PNGs are genuine Fuse captures, not archive reference pictures. No native game was built.

Source SHA-256:
Outlander.z80 c03efebe2e0073f02c2616df02936eab639606367a3834bf58eb8cc16ea6e9cb
Outlander.tzx 28d39adb0ea3a478077fc6f20b905d83fe1b7289205eec5457c3a3034572c9c8

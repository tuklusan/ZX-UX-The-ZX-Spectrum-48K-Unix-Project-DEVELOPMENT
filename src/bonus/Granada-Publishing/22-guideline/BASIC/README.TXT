GUIDELINE — GRANADA PUBLISHING

We kept the original Guideline.tzx and SpectrumGuideline.tap from the Granada Publishing archive. The two recordings carry different tokenized BASIC programs: 1,603 program bytes and 74 lines in Guideline, versus 1,546 bytes and 71 lines in SpectrumGuideline. We regenerated both listings with the ZX-UX ROM LLIST converter. The original bytes were preserved.

Both programs are versions of the same guiding-ring game. The player steers a small ring along a drawn line and tries to stay on target. The title, line drawing and the 6/7 controls match. Some text and scoring routines differ. We count the two versions under one distinct program folder, with each source listed separately.

We started both original recordings in genuine Fuse 48K, selected difficulty 2, then pressed 6 and 7. Four real screenshots show the ring and the line while each original program runs. We did not finish either full run or confirm a final accuracy score.

REPLAY-GUIDELINE.sh and REPLAY-SPECTRUM-GUIDELINE.sh run the two originals at Fuse speed 200%. No native binary is included.

Guideline original TZX SHA-256: 574c762a26a9186b3f84a241d42b53c9e5fc4e3e276241a21968c637ceea9bc8
Guideline regenerated BASIC SHA-256: 30a048115125f84a9a0d78062af26ac7cfc1fa6bbfae8a1f599a82a0d46d9a62
SpectrumGuideline original TAP SHA-256: 985de7bcff08e29f5e8063a0abb888fd10e8552f4b1f37d3dd5d90fb6f7c22ff
SpectrumGuideline recreated TZX SHA-256: 341c4636f1783420e155496b6d731dec4d980023ea0004510125781ba1205eee
SpectrumGuideline regenerated BASIC SHA-256: 616d84929dfaae09ebd1ebb944e7bf2dd152a86ab41099682eb2660d84c12512

Run each replay from the repository root:
  sh src/bonus/Granada-Publishing/22-guideline/BASIC/REPLAY-GUIDELINE.sh
  sh src/bonus/Granada-Publishing/22-guideline/BASIC/REPLAY-SPECTRUM-GUIDELINE.sh

Fuse SDL, Xvfb, Python 3, Pillow, python-xlib, and the ZX-UX 48K ROM are needed.

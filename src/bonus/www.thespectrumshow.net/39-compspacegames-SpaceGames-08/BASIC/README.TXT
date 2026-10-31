ALIEN SNIPERS — Computer Spacegames, eighth program

We preserved the supplied program-specific SNIPERS.tap and SNIPERS.tzx without changing their bytes. The master 15-program SpaceGames tapes and Info.txt are already with SpaceGames-01. We decoded 23 numbered BASIC lines from SNIPERS.tzx using the ZX-UX 48K ROM LLIST tool.

The program asks for a difficulty from 1 to 10. In each of ten rounds, it displays a letter and a number. BASIC line 190 scores a hit when the pressed letter is that many places after the displayed letter. Each target lasts for a short loop, so the player must respond quickly. Line 210 reports the total hits out of ten.

We loaded the TZX in Fuse 48K, entered difficulty 1, then sent A and C while targets were appearing. We captured the input screen, target and later target views. The letters and targets change automatically between rounds, so the screen changes alone do not prove that either key scored a hit. We did not confirm a full ten-round result. The aliens need not celebrate yet.

SCREENSHOTS/ holds genuine Fuse captures, not the supplied reference images. REPLAY.sh requires Fuse SDL, Xvfb, the ZX-UX 48K ROM, Python 3, Pillow, and python-xlib. No native output was built.

Source SHA-256:
SNIPERS.tap 0118dfa261c88c9029f049c5cf6b3cdcb996ca35de59c84d58198265c2e0ee9a
SNIPERS.tzx 0524c170f5f002fb333bfe68f327e1d1e88bce1ae054a62a45e649beeb4e8528

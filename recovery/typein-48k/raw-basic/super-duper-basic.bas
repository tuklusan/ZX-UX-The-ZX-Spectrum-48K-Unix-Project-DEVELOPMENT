p  g
 part ofthe line that has failed syntax must   "pait2" Code59904
 be moved to a new line.                     After verifying p
  The ZX! Basic screen is different to that  can be loaded bac
 ofSpectrum Basic.For the two new print
 commands the top left hand comer ofthe
 screen  is  coi\sidered  as  0,0; and the      KEXOUMP  * HEXLD
 bottom right hand comer as 23,31; that is
 the GBP"<?7lines are part of the main screen
 and not just for ihpufcommands.               2010 REMREM *?HEX
  The new commands for plotting, ie, !P,        30 REM
 ID,.'C,IN,!Bu3ea25S x 256pixel screen        40 DEF FN CO
 in which pixel  0,0  is  the bottom  left        80 DEF FN DO
comer pixel (line 23) and 255, 191 is the        6070 DEFDEF FNFN FOEO
 top right hand comer. 'Y' co-ordinates        80 DEF FN AO
between 192 and 255 are allowed but of        90 DEF FN BO
course will be  off the top  of the TV        100 DEF FN C?0
 screen. This  is useful when lines are         ?N'CFN+7*(FNBOAO>9?>+>9)  )
reqmred to go off screen and then back       110 PAPER 7!   I
on again.                                     120 INPUT 'Fro
  ZX! Basic is loaded in two sections and       L)  "|8T
comprises approximately 7K bytes of       130 INPUT "To
code with a further 6.25K allocated to       140' (ENDPAPER 7!   I
Sprite data (which includes a screen       1S0 FOR X-ST T
dump when animation is switched on).         160 LET Y-FN C
  To enter the machine code use the                  I
following simple Basic program which in       180170 LETLET T-0Y-FN D
fact has two functions:                         190 FOR Z-0 TO
 1. Goto  10  -  prints on  the screen a       200 IF X+2>END
                                                      O TO 240Hexdump  of any area of memory in
blocks of eight bytes with the Hex ad        210 LET Y-PEEK
dress of the first byte in the block and       220230 PRINTLET T-T+YFN C
also  prints a Checksum byte  for  the       240 NEXT  Z
block calculated as the sum of the previ        250 LET Y-FN F
ous eight bytes 'mod. 256", that  is the      CSO  t
remainder of the sum: Sum of 8 bytes/      EXT260 X IF X+Z<-END
256.                                         270 PRINT   ? ZZ
2. Goto 1000- allows the input of blocks       280 STOP
of eight Hex numbers and the Checksum       290
byte  (ie, a Hexloader).  If any  line  is       300
incorrectly entered then there is  suffi       1010 REM * HEX
cient error trapping to detect this and
give a suitable error message; the line      1030 OEF FN 0{A
can  then be  re-entered.  Each  input      S-7*(CODE A?(B)>                                            1040 DEF FN H(A
should consist of 18 characters except      FN 0(A  2
g       however attributes can be changed to redi
 4,5464.                    rect  sprites.  (This  is  discussed further  in
  art 2, the two codes   commands !F, IG, !H, !J,and IK)
ck into the Spectrum     !A0 turns off the routine, while !A> 0 turns


                        10S0 PAPER 7:  INK 0; CLS
 DADER                 1060 LET RC-*0-
                        1070 INPUT "Start address (DECIM
                           AL)  -lADR
                        1060 PAPER 7;  INK 0: CLS
 XDUMP+CHECK8UM **     1090 INPUT "8 BYTES+CHK  "IBS
                        109S LET ST-ADR
O-INT  (X/2S6>          1100 LET LEN-LEN BS:  IF  (INT  (LE
O-X-FN C<?*2S6                        N/2>*2<>LEN) THEN  PRINT "Odd no
O-INT  (T/2S6)                         ?o* chrs.  'i: go to 1330
O-T-FN E??*2a6                        1110 IF LEN-18 THEN  00 TO 1130
O-INT  <Y/16J           1120 IF B?(LEN-1 TO K>"ZZ* THEN
O-Y-FN AO*16           PRINT  "No  'ZZ' marker  "fi BO T
 0-CHR?  (FN A()+48
 CHR?  (FN 80+46+7     O 1330
                        1130 FOR a-1 TO LEN-2:  IF BS(A)<
                                  ?0"  OR B?(A)>"F" THEN  PRINT "In INK 0: CLS
on address (DECXMA    valid chr.  'i; 60 TO 1330
                       1140 IF B?(A)<"A? AND B?(A)>"9'
                        THEN  PRINT "Invalid chr.  "i: 60  addrasB  (DECIMAL)
                         TO 1330
 NK 0; CLS             1190 NEXT A
 TO END STEP  8          1160 LET X-ADR
 CO; PRINT FN C?0     1170 LET Y-FN CO! PRINT FN CSO
                                                                           \
                       1180 LET Y-FN DO; PRINT FN C?0
DO  PRINT FN C?0                       1200 LET X-0
                       1210 FOR K-1 TO  8O  7
D THEN  LET z-e:  3     1220 LET A?-B?(  TO 2>: LET B?-B?                              (3 TO   )
                        1230 IF B?--ZZ" THEN  LET K?9!  LK  (X+2)
                        ET R?-BS; LET B?-Aa; 60 TO 1260
C?0|*  ?|              1240 PRINT A?|-  *1
                       1250 LET P-FN H(A?)
FO! PRINT    "IFN     1260 LET X-X+P
                       1270 POKE ADR.P! LET ADR-ADR+1
 D THEN  PRINT    N     1260 NEXT K                       1290 LET Y-FN DO; PRINT   ???  "IFN
  ?                  CSO I "/"IBS
                       1300 LET A*-B*
                        1310 IF Y-FN H(A?) THEN  60 TO  1
                      350
                        1320 PRINT "CheckBUtn  "l
 1/P UlTH CHECK  *      1330 PRINT "error   -  re enter":  B
                       EEP .3,10; BEEP 1,5; LET ADR-ST
 ?,B)?C0DE A?(B>~4     1340 QO TO 1090
 >57)                  1350 PRINT "OK": BEEP .1,20
A?)-16*FN G(A?,1)+     1360 IF RSO'ZZ" THEN  GO TO 109
                                            0
on the routine. (Note: if this is used as a direct   which 15 are computer
command then be prepared for sprites in   being controlled from th
your listings!)                                cursor keys. Each of the
 Bx,y,xo,yo  - Draw a box using  the  co     set  of sprite attributes
ordinates x,y and xo,yo as the two opposite    follows:
corners of the box. This command uses the   n  - sprite no, (1 to 16)
current    colours.   For   example,    10    s  - speed 0 to 255 (the
 .BO,0,255,191, 20 Pause 0 will box the whole    faster the sprite) use va
screen. The Pause 0 instruction being neces     63, 127 and 255 for smo
sary to stop the report 'OK'on the Editlines.    values will give jerky m
 Cx,y,x, - (Circle)                                 lo  - line offset value. 0
Draw a circle with centre x, y and radius r.    cally, 1 is down, 255 is u
The values of jrand yean be from 0 to 255, and  CO - column offset horiz
rcan be from 0 to 100. This command is many    is left.
times faster than the Spectrum circle and   1 - start at line (0 to 23)
allows part circles to be drawn without the    c  - start at column (0 to
 'Out ofScreen'error report.                         b   -  value of screen attr
 Dxo, yo - (Draw)                            bounce, (0 to 255).
As with Spectrum Basic, this will draw a line    f - figure to be used for
from the current plotted pixel to that specified   ZXlBasic has 16 differen
by X offset, y o^et. However with this com   used or you may desi
mand the offset value can be off the screen   using the ZXlSprite Des
and will wrap around as necessary. Colours   printed later in the serie
are supported as with Spectrum Draw. Note   character squares and c
that the current co-ordinates are taken as on   pixel to 16 X16 pixels.
the ZX! Basic grid.                               the initial movement of
!E - (Erase)                               change on striking a ba
Erase all 24 lines using the current attributes.    set up then the sprite
This is similar to Cls but does not reset the   screen.
print position to 0,0.                            !Gs, n - (Go)
IFn, s, lo, 1, c, b, f- (Format)                   Switches On/Off a spri
The  first  of the Sprite handling commands   been formatted using IF
used to set up a Sprite prior to turning on that    the screen or taken of
sprite (see !G).                          command, s is the sprit
  There are 16 sprites available in ZXlBasic of   and n turns it on/off (0 is


   Z;< Spectrum 48K HEXDUMP             CB0A  00 22 44 44
  Part   1      :  CODE 51650,2100            CD12  OO 22   1   11
  C9C2  CD 14 25 F5 CD F5 F6 CD    =  7E  CDIA  00 00 5S 22
  C9CA  0D FO F1 32 3F 5C ED 43    =  43  CB22  00    22 22
  C9n2  7C CA CD DC FD C0 21 00    =  CD  CD2A  00 00 00 00
  C9DA  00 72 7A CA ED 4B 7C CA    =  E4   <;332  00 00 00 00
  C9E2  OC 79 A7 28 07 C5 CD DC     =  C9  CC3A  00 00 00 00
  C9CA  FD C1 28 F4 0D 21 01 01                          -  0A  CB02  O0  11   1 1 22
  C9F2  22 78 CA ED 43 7C CA CD    =  A7  CB4A  00 33 55 55
  C9FA   tr2 F6 ED 4B 7C CA 78 3C     =  0A  CB52  00 66 22 22
  CA02  FE C0     IF 47 C5 CD DC     =  BA  CB5A  00 22 55 11
  CAaA  FD C1 28 05 32 78 CA 18      s  77  CB62  00 77  11 22
  CA12  12 3A 7B CA A7 28 0C CS      s  2E  CB6A  00 44 55 53
  CAIA  2A 7A CA 23 22 7A CA AF     s  A6  CB72  00 77 44 66
  CA22  32 78 CA ED 4B 7C CA 78     =  6A  CP7A  00 33 44 66
  CA2A  3D FE FF 20  IF 47 CS CD               -  5A   CB32  00 77  11  11
  CA32  DC FD C1 28 05 32 79 CA    =  3C   CB3A  00 33 55 22
  CA3A   19 12 3A 79 CA A7 28 0C     =  82   CB92  00 22 55 55
  CA?12  CS 2A 7A CA 23 22 7A CA      a  BC   CB9A  00 00 00 22
  CA4A  AF 32 79 CA ED 4B 7C CA    =  A2   CPA2  00 00 00 22
  CA52  OD 79 FE FF 23 0E C5 CD    =  4B   CBAA  00 00 11 22
  CA5A  DC FD C1 28 96 CD 54 IF    =  90   CBB2  00 00 00 77
  CA62  3Q 02 CF  14 2A 7A CA 7C       s  07   CBBA  00 00 44 22
  CA6A  B5 C8 2B 22 7A CA C1 ED    =  DC   CBC2  O0 22 55 11
  CA72  43 7C CA C3 E2 C9 01 01       s  F9   CBCA  00 66 DD DD
  CA7A  00 O0 78 74 21  17 C6  IE     =  08   CBD2  0O 22 53 55
  CA82  C1 C9 49 F3 D0 F5 O0 35     o  C9   CBDA  00 66 55 66
   CA8(".  AA 55 AA 55 AA 55 AA 35    =  FC   CDE2  00 33 44 44
  CA52  AA 35 AA SS 00 00 00 00   FE   CBEA  00 66 35 55
  (:A9A  O0 00 00 00 AA 55 AA 55    =  FE   CBF2  00 77 44 66
  CAA2  FF 99 99 99 99 99 99 FF     =  94   CBFA  00 77 44 66
  CAAA  00 66 66 66 66 66 66 00    =  64   CC02  00 33 44 44
  CAE2  00 00 FF 99 99 FF 00 00   30   CC0A  00 55 55 77
  CABA  00 00 00 66 66 00 00 00    =  CC   CC12  00 77 22 22
  CAC2  00 O0 66 FF FF 66 00 00    =  CA   CCIA  00  11   1 1  11
  CACA  00 00 00 00 00 00 00 00    =  00   CC22  00 55 55 66
  CAD2  00 22 22 22 22 00 22 00  s: AA   CC2A  00 44 44 44
  CADA  00 55 55 00 00 00 00 00     s  AA   CC32  O0 53 77 77
  CAE2  O0 03 55 77 55 yy 55 00   ED   CC3A  00 66 55 53
  CAEA  00 22 77 66 33 77 22 00    =  CB   CC42  CO 22 53 55
  CAF2  00 CC DD 22 44 BB 33 00    8  FD   CC4A  00 66 55 55
  CAFA  00 66 AA 44 B6 AA DD 00    =  96   CC52  O0 22 53 55
  CB02      22 22 0O 00 00 00 00   44   CCSA  00 66 55 55
r controlled, the 16th   !Hs, n - (Speed)
 he keyboard using the   Changes the speed of a sprite. The sprite can
 ese sprites has its own   be on screen or off. sis the sprite in question.
 s  (sets up by  !F) as    (1 to 16) and n the new speed value (see !F).
                            !Js,n - Oump)
                     Changes the figure used for a sprite: s is the
 e lower the value the   sprite in question (1 to 16) and ji is the new
 alues 0, 1, 3, 7, 15, 31,    figure, (1 to 16).
 ooth movement, other    !Ks,ii - (Knock)
movement.            Changes the barrier value for a sprite: s is the
  is no movement verti    sprite in question (1 to 16) and n is the new
 up.                    screen attribute for barrier, (0 to 225).
 zontally, 1 is right, 255    !Ix,y,n - (In fill)
                          This command will paint any shape starting
                      from co-ordinate *,7using colour as specified
  31)                by attribute value  Ji. Any shape however
 ribute that will cause a    irregular can be filled quickly, but ensure that
                          the shape is complete with no gaps for the 'fill'
  r sprite. (1 to 16)          to escape through. The command has a Break
  nt figures that can be   routine built in 'just in case'.
 ign your own figures   For example, 10 !C127,96,40ZQ !I127.96,56vn]l
 signer program to be   draw a circle in the middle of the screen then
 es. All sprites move by     fill it in black.
 can be any size from 1   !L address,n - (ZXIPoke)
  Offset values control  A special Poke instruction to allow the setting
 f the sprites. This will   up  of sprite  figures. The Spectrum Poke
 arrier. If no barrier is  command will result in a pareimeter error
  will wrap around the   report  if attempts axe made  to Poke into
                       addresses S1650 to 65359. Address between
                        51650 and 65359 and ji has a value 0 to 255.
  te. Once a sprite has   Remember,   to   install  ZXlBasic,  use  the
 F then it can be put on   hexloader printed this week to load the data
  f the screen with this    that  will be published over the following
 te in question (1 to 16)   issues.
  s off, > 0 is on).         Next week, more instructions and more data.


  44 44 22 00    =  54  CC62  00 33 44 22 11  11 66 00      s  21
     1  I    1   22 00   88  CC6A  0O 77 22 22 22 22 22 00    21
  77 22 35 00    =  63  CC72  00 53 55 55 55 55 33 00    =  DC
  77 22 22 00    =  FF  CC7A  00 33 55 55 55 55 22 00    =  CB
  00 22 44 00    =  66  CC82  00 33 55 55 77 77 55 00    =  42
  77 00 00 00    =  77  CCSA  00 S3 35 22 22 55 55 00   98
  00 00 22 00    =  22  CC92  00 33 55 55 22 22 22 00    =  63
  22 44 44 00    =  EE  CC9A  00 77  li 22 22 44 77 00    =  87
  55 55 66 00    =  ED  CCA2  00 66 44 44 44 44 66 00     =  DC
  22 22 22 00    =  10  CCAA  00 44 44 22 22  11  11 00    =  EE
  22 44 77 00   65  CCB2  00 33  11  11  11  11 33 00   as AA
   11  11 66 00    =  32  CCBA  00 22 77 22 22 22 22 00    =  21
  77  1 1  11 00   87  CCC2  00 00 O0 00 00 00 00 FF    =  FF
     1 1  11 66 00     =  A9  CCCA  0O 33 44 66 22 44 77 00    =  BA
  55 35 22 00   A9  CCD2  00 00 66 11 77 33 77 00    =  BA
   22 44 44 00    =  43  CCDA  00 44 66 55 55 55 66 00    =  0F
2 55 55 66 00   BA  CCE2  00 00 33 44 44 44 33 00    =  32
5 33   1 1 66 00    =  76  CCEA  00  11 33 33 35 33 33 00    9  76
 2 00 22 00 00   44  CCF2  00 00 22 33 77 44 33 00     a  65
 2 00 22 44 00   =  88  CCFA  00  11 22 77 22 22 22 00       -  10
 2 44 22 11 00    =  AA  CD02  O0 00 33 55 55 55 33 66    =  CB
 7 00 77 00 00    =  EE  CD0A  00 44 66 55 53 33 55 00   B  FE
 2  11 22 44 00    =  DD  CD12  00 22 00 22 22 22  11 00    =  99
   22 00 22 00              -  CC  CDIA  00 22 00 22 22 22 22 44     =  EE
 D 6B 88 77 00   DA  CD22  00 44 5S 66 66 55 53 00   0F
 5 77 35 55 00   ED  CD2A  00 22 22 22 22 22 11 00    =  BB
 6 55 55 66 00    =  31  CD32  00 O0 55 77 77 55 33 00    =  ED
 4 44 44 33 00    =  76  ':D3A  00 00 66 53 35 35 33 00    =  BA
 5 33 35 66 00    =  20  CD42  00 00 22 55 55 33 22 00    =  43
 6 44 44 77 00    =  20  CD4A  0O 00 66 55 55 55 66 44     =  0F
 6 44 44 44 00   SS ED  CD52  00 00 33 55 55 55 33 11   8S 76
 4 33 33 33 00     a  98  0D5A  00 00 33 44 44 44 44 00    =  43
 7 53 55 55 00    =  20  CD62  00 00 33 44 22  11 66 00    =  10
 2 22 22 77 00   76  CD6A  00 22 77 22 22 22 11 00    ??  10
 1   1 1      t 1 66 00    =  BB  CD72  00 00 53 55 33 33 33 00    =  87
 6 55 55 53 00   0F  CD7A  O0 00 55 55 55 55 22 00    =  76
 4 44 44 77 00   =  CB  CD82  00 0O  3!) 53  :?7 77 55 00   ED
 7 53 33 55 00    =  42  CDSA  00 00 55 55 22 35 33 00    =  76
 3 55 55 55 00    =  0F  CD92  00 OO 55 55 55 33 33 66    =  ED
 5 33 33 22 00   98  CD9A  00 00 77  11 22 44 77 00    =  63
 5 66 44 44 00   =  FE  CDA2   11 22 22 44 22 22  11 00   EE
 5 55 77 33 00    =  CB  CDAA  00 22 22 22 22 22 22 00       ?  CC
 5 66 55 55 00   20

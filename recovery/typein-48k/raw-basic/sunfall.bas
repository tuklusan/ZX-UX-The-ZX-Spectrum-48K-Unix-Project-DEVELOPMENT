1000 LET  leve  I  s Leve  I ? (leve  I <23)
23*(leveI>=23);  POKE 32538^level
*8+70j  LET a=USR 3SS00;  LET time
 = 0
1010 LET sxsS:  LET cxs2:  LET sys
INT  (RND*6)+3;  LET CU^INT  (2S-.RW
D*6):  LET r*(1,sy*3+1 TO sy*3+3)
=S$;  LET r$(l,cy*3+l TO cy*3+3)=
S $
1020 GO SUB 7000: PRINT    ?*   L:";   f
"0" RND  leveL<l0); level;"  B:"Jb
reaks.:"     INK  6;  BRIGHT   1.; "#***
 "   ( TO suns);  BRIGHT 0;TnB  l:  PRI
NT RT 2^0;;  FOR a=l TO 20: PRINT
    r $ (a)   ;  NEXT   a
2000 PRJNT      c.x,cy;  INK
T  sx,sy;  BRIGHT  1;  INK 6;"*"
2010 LET i$ = INKEY$:  IF    i $<>'?" TH
EN LET  tiiaea0:  IF  i$=s'h  - THEN PR
INT ?0;  FLRSH 1;"HOLDING": PAUSE
  0;  INPUT ""
2020 IF i$="0" THEN IF SX<21 AND
 breaKs THEN PRINT RT sx+l.sy;     I
NK 0;"    LET breaKs=breaKs-1:   P
RINT RT 0,26;breaks:  LET r${sx^s
y*3 + l  TO sy*3+3)=:s$
GBP030 IF  i!fe<>"S" AND i$<>"(C)" THEN
 LET     t   i jne =:t  i me+1:  IF tiB)e>15~lev
el THEN LET i$="S":  LET time=0:
IF RND-{.5 THEN LET    i $ = "S"
204.0 IF  i$s="5" THEN LET r$fsx-l)
ssrt(sx-l,4. TO )+r$fSX-l, TO 3);
LET sy=sy-1+32*(NOT sy): LET cya
cy-l+32*(NOT cy):  IF sx<>cx THEN
 LET    r $  ( cx-1) =r $ (cx-1^4. TO )+r$(
CX-1, TO  3)
20S0 IF i$s"8" THEN LET r$Csx-lJ
ar$(SX-l,94. TO )+r$(SX-l^ TO 93)
 :  LET syssy+1-32*(sy=31): LET cy
aCy+1-32* (cy =31)   :  IF sxocx THEN
 LET r$ (cx-1) =r$ (cx-1^94. TO )+r^
 (CX-1, TO 93)
2060 IF i?="5" OR i$="S" THEN BE
EP .02^-10:  PRINT RT sx^0;r$(sx-
1): PRINT RT cx,0;r$(CX-1)
2070 IF RTTR  fsx+l/sy)<>12 THEN
BEEP .01,30:  PRINT RT sx,sy;  INK
 0;"         :  LET sxarsx+l:  LET score=S
core + level + leve1*9*(RTTR  (s x,s y)
al3):  PRINT RT 0,7-LEN STR$ SCOT
e;score:  IF sx<>22 THEN LET r$(S
x-l,sy*3+l TO sy*3+3)=s$
20S0 IF RTTR  (cx+l,cy)<>12 THEN
BEEP .01,10: PRINT INK 0;RT CX,C
y;"  ": LET CXaCX+1:  IF CX<>22 TH
EN LET r$(CX-1,cy*3+1 TO cy*3+3)
?s $
2090 IF SX022 RND  CX < >22 THEN  (C)
O TO 2000
2100 IF CX=22 THEN LET suns=sun&
-1;  IF SOnss-1 THEN PRINT RT 9^9
;TfiB 21; RT 10,10;"    FLR3H 1;  B
RIGHT l;"GRME OUER";  BRIGHT  0;  F
LRSH 0;" ";RT 11,9;TRB 21:  GO TO
 5000
2110 IF CX=22 THEN BEEP .1,10:  B
EEP  .1,4.:  BEEP .1,0:  GO TO 1010
2120 LET drOps=dropS+1:  IF drops
=5 THEN LET drops=0:  LET score=S
 c o re + 100*level  LET  levelsslevel +
1:  GO SUB 6000  GO TO 1000
2130 BEEP .1,0  BEEP  .1,4.:  BEEP
.1,10; LET SX=2:  LET r$(sx-l,sy*
3+1 TO sy*3+3)=s$:  GO TO 2000
3000 DRTR        " ,254-, b  , b, b   , b, b   , b,0
3010 DRTR "^",0,16,4.0,68,68,56,0
  , 0
3020 DRTR     ,4.8,72,72  , 132 , 130, 1
14.,12,0
3030 DRTR "*", 16,84., 56,254", 56,84.
  . 16,0
304.0 INK  7:  PRPER  1: BORDER 1:  C
LERR 324.99:  DIM r$(20,96): PRIMT
 RT 10,8;"Hang on   a second"
3050 FOR C=1 TO  4.;  RERD a$:  FOR
a=USR a$ TO USR a$+7:  RERD  b: PO
KE a,b:  NEXT  a:  NEXT   c
3060 RRNDOMIZE     :  LET hi=0: LET  S
$=CHR$ 16+CHR$ 0+"   "
3070 DRTR 1,127,3,4.2,75,92,17,8,
0,25, 229 , 4-2 , 118, 92 , 84., 93 , 4-1  , 4>1, S
5, 4-1, 4.1 ,4.1 ,25,34., 118,92, 124-, 225/
254. ,25, 4.8,5, 17 , 5, 14.5,24^  , 12 , 254. , 8
 0   , 4.8 , 5   , 17 , 0   , 32 , 24., 3   , 17 , 4-, 14.4. , 54.,
16,35 , 115,35 , 114., 35, 11 , 120,254-, 0
 ,32,204.,201
3080 FOR a=32500 TO 32562: RERD
 b:  POKE a^b;  NEXT   a
3090 PRINT RT 10 , 7; " Ir/s t  r u c  t  i ons
?   y^n":  PRUSE  0:  IF INKEY$="y"
THEN GO SUB 8000
3100 OLS
4.000 LET drops=0:  PRINT ?0; "   Se
lect  level  of play:   1  to S"
4.010 PRUSE  0:  LET i$ = INKEY$:  IF
i$<"l" OR i$>"6" THEN GO TO 4-010
4.020 INPUT     LET level=URL     i  $  .?
 LET SCOre=0: LET sLins=4.-INT  ((I
evel-l)/'2):  LET  br e a K s =10-1 e ve I:
 GO SUB 1000:  IF score>hi THEN  L
ET   h   i as C D  r e
4030 GO sue 7000:  GO TO 4-000
5000 FOR aa60 TO  0  STEP  -2:  BEEP
  .02,3:  BEEP .02,a-10;  NEXT a:  R
ETURN
6000 FOR aa0 TO 60 STEP 2:  BEEP
.02,3:  BEEP .02,3-10:  NEXT  a:  NE
XT   a
7000 PRINT RT 0,0;"S:00000";RT  0
,7-LEN STR$ score;score;TRB 9; "H
:00OO0";RT 0,16-LEN STR?  hi.  h  i   ;   ;
 RETURN
SO00 CLS     : PRINT "SUNFRLL"'  "(C)  1
983  by J.Medhurst      This game_
  is played on  a scrcenthat has  2
0  rows of green blocKs";  INK  4-;**
     INK 7;",  with gaps  in  them.
The aim ofthe game  is  to slide     t
hese  rows across  to enable your
sun;  ";  ink 6;"*";  INK 7;"  to dr
op  from  the  top  of  the screen"
8010 print "to  the bottom throug
h  the spacesin  the   b lo c Ks   . There
  is also   a      c loud;  ";  INK  3;"fl>";
 INK 7;" Which you must prevent
from dropping  to  the  bottom,  if
you  don-'t you will  loose   a sun."
8020 PRINT   "  Uhen you reach  the
bottom you   are transported bacK
  to  the  top until you have done
five drops,  after which you  reci
eve 100      times  the  level numb
er  in pointsand  go onto  the next
  leve  I ."
8030 GO SUB 9000:  PRINT   "  For ea
ch  row of blocks you movedown yc
u  get  the  level number inpoints
and  if there  is   a  rain    drop;    "
 ;  INK 5;"6 "   INK 7;"  in  the  the
gap  the sun  drops  through you    r
eceive  ten    times  that number   o
 f  points."
804.0 PRINT    If you  find  that yo
u  are unableto  find   a  gap  to dro
P  through    then you  can press     t
he  '0'  Rey   and  the block under
you will  be disintegra ted. You   c
an only do   this   a  small number
of     t  i mes  ,    and  the number you  h
ave  left  is shown on  the  top row
 after  the   letter  'B'."
8050 PRINT   To move  the  rows  Ic
 ft and rightyou use  the  '5'  and
 '8'  keys     respectively, doing
so will movethe  row  the sun  is     i
 n  and  the    cloud's  row  in  the   g
iven direc-  tion.  If  this places
 either overa space  then  they  wi
 II  fall."
8060 GO SUB 9000: PRINT   " The hi
gher  the  level  the  less  blocks
there are which makes  it more  dx
 fficult  to stop  the cloudreachin
 g  the  bottom  To~   make     things
worse;  after   a  set  time;  Wh i Ch   g
ets smaller,  of not mov- ing   a     r
ow,  the  rows  ttove  in   a    random
direction."
8070 PRINT   "  Rt any  time you may
 press  'H'   which  wi II hold  the
game until     a  key  is pressed  .  Uh
ilst you areplaying  the  top  line
   o   f  the     screen will show,  fr
om  left  to   right  Your score,      t
he highest   score.  the  leve  I   ,  th
 e  number   o   blocks you  can  blast
  j  and how   many suns you have    I
eft. e.g."
8080 PRINT   "5:024.96   H: 04-912    L
   : 04.   B: 4.     INK 6;"***"'  INK 7'"
 You Will how  be asked  at which
 level you wish  to start on."
900(C) PRINT ttO;"Press any  key  to
 continue.": PRUSE 0:  BEEP .2,0;
BEEP  .15,-4.:  INPUT     CUS    : RET
URN

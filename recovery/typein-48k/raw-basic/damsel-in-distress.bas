eORDER (C); PAPER  0;  INK 7  0
 "3500 LET Ss0;  LET  K -3
    "36 PRINT  "p Lease wait.";  re3to
RE;    : GO'SUB(SO SUB 9500QF>n<7i
^^4-0 GO SL'e 9000;  REM  Zn=tri.'CtiO
  S0 BORDER  4;  PftPER  4;  INK  0;  C
LS      ;  BRIGHT   0
  t0 INPUT  "Level 1-9   ??   1*9 easyJ
  "J       ;  IF  l:-3 THEM SO  T'J SS
  ei  INPUT  "SkilL    or        7    (tf ea
sy)  "^rS:  IF r$="B- THEN LET  rti =
"b"
  70 PRINT AT 0^0; "Leve L ;  ??;    I  ;  PR
INT RT 0,16;"Score="; s
  50 DC'iMT  <3-r  1       ? "M M     '  f   '  I  f T ? j-h*
M j M I i W 1n   i M i JYI ri-    ??=OR    i =a to
;?.:19^.*iE;<T.:  PR INT.i.;. ATPR.INTi /S;^ "H"  ' j I I Ii I>31j.I I f I I
 iio FOR i=? TO  13-10 + 1(C)
 120 1-GBPT M=lNT  tRNDilS) +2:  LET  y
= INT  (RND*^30) -f-l;  PRINT RT X,y;    I
HK 0;"*":  NEXT     i                              _
 140 PRINT RT 4.24;  INK  7; A    :  P
RINT RT 5,22;  INK ,7;        PRINT
 RT 6.22;  INK   7.; "ill"  I"
 160 LET y=INT  (RNDt30)+1;  LET X
 = iei:  PRINT AT x.y;  INK  7;'"ff"
 170 LET  d;:=INT  iRNDiie>+2; LET
dy=I/-JT  CRND5-G0.- +1:  FRINT  HT UX y d
y;  INK  2; "V
 210 REM Movement
 21s IF rS = "t>" THEN FOR  1 =1 TO  2
 220 LET  f=0;  LET h=0
 230 LET   f = r-{INKEY$ = "7") +(INK.E>'
 ^240 LET h=h-CINKEY$="5:"J +(INKEY * = ?? S  "  .1
  245  IF INKEY$ = "(C)'" THEN GO SUB  5
 0OO;  REM Kill Right
  250 PRINT RT X . y;   "?    "  :  IF RTTR    (
 X+f,y+h)=39 THEN GO TO 2000                 '
  260 IF SCREENS (X+f^y+hJO      T
 HEN GO TO 500
  2-70 ORIN"^ RT   v;  . U ;  "  ".  LET X    + r
  ; LET y=y+h:  PRINT AT X,y;  INK  7
 '2^5 IF r$="b" THEN NEXT  i
  280 GO TO 500
  500 REM Knights  ffiova
  510 PRINT hT x>y;  I/iK  7;   Z-"
  520 LET O^Q:  LET P-<2
  530 LET 0=0-fdy>yi + idy<yj  :  Ir  S
 CREENS  (dx^dy+OJ<>"   " THEN LET O
 =0.  GO TO 540
  535 GO TO 570
  540 LET p=p+(dX<X)-(dX>XJ          _
  570 IF dx+P=X RND dy+0=y THEN G
 D TO 3000        ?                                                      ..
  SS0 IF SCREENS     i dX+P y d y 4-0 ) <>
  THE^i GO TC 210                                                     ,
  5S0 PRINT RT dX^dy;'-   "  : LET dy =
 dy+O;  LET dx=dx+p-. PRINT RT dX^d
 y;    , INK 2;"^";  GO TO iJl0
         CtTL'P
 2000 REM  Hoaie
 2010 PRINT RT X^y;  INK  7;
 2020 FOR i=30 TO 5(C) 6TEP 2:  BEEP
   .1  .  i   ;  NEXT    i   ;  FOR    i =50 TO 30 ST
 EP  -2;  BEEP .l,i;  NEXT     i
  ;:^03(C) LET s=3 4-l(C)
 GBP040 PRINT RT X^y;"    "
 2050  IF' 1>1 THEN LET   1 = 1-1
 2055 FOR i=23 TO  2 STEP  -1; PRIN
 T RT 7,1+2;"     PRINT RT        , x;    I
 NK 7;"^i".  PRUSE  5;  NEXT    i
 2060 CLS
 2070 GO TO 70
 2399 STOP
 300(C) REM Caught  by KNIGHT
 3010 PRINT RT d.x,dy;"         . PRINT  ft
      d;.<-rp ^ d y-j-o ;   u'.'ER  l;
 302(C) PRINT RT dx^dy;       '    *?
 3030 FOR i=-30 TO -20 STEP S; BE
 EP .1.i; NEXT  i;  PfiUSE 21.  FOR    i
  = -20 TO -30 6TfcP  -a;  tSEEP .l,i;
 NEXT  i;  FOR i=(C) TO 50 STEP 5;  BE
 EP  .1,i.  NEXT     i
 3040 eOROER  0:  Pi^PEft  B:  INK      C

 3Q50 GQ TO 400(C)
  .3QQ1C1 .STOP
 ^000 REH Gdme over
 4010 FOR a=0 TO 21:  PRINT RT a>a
    ;  INK 2;"Gase over";  PRINT RT 21
  ~a,a;  INK  2; "'Gaiae Over":  BEEP  .1
  ,a;  NEXT   a
 402(C) FOR  i=-E.0 TO 50 STEP 10; BE
 EP       NEXT  i:  PRUSE S4
  4-030 CLS
 4040 PRINT TRE 10;  I^^K  6; "Gaas  O
  v-sr-'TRB 10;  INK 6;"                       "
 -050 PPINT                            ??     The Knight has   c
 aught you and    taxen you bacK    t
  o  his dungeon.   Frota which you  w
  itt never       escape."''"  You
   Bianaged  to  recue  the         Daw
 seI ";s/l0;"  tiaes^which means"'
     Mou scored "is;" points."
  gisEia PRINT       Dq you want  to  p
  lay again  7"'-'  presi  Y  for  yes
    ?;-r  N  for  no.  "
  4070  IF I?iKEY$="V" OR INKEYS = "y
  THEN LET S=0;  GO TO 50
4030 GO TO 4070
4.-30-S   --T-np
5000 REM Kill Knight
5010 LET R=K-1:  IF K<=0 THEN RET
IJiSNJ
S020 PRINT RT dX,dy;     '   "             _
5030 LET dX=INT  (RND3rlSi+2:  LET
d'i=X'-ii   iRNr-x30.*  ???1
S035 FOR     i =50 TO 30 STEP  -S; SEE
P  .1,i;  NEXT     i               ^
504(C) PRINT RT dx>dy;"V"
5050 RETURN
9000 REM Instructions
9010 PRINT RT 1/6;  INK 2;"DaffiSe I
  in Distress"'  INK GBP;"

9020 PRINT RT 4,6;  INK 2;"(C) Rich
ard Bartlett 1983"
9030 PRINT RT       Collect  the
damsel  From  the"''" castle  to sc
ore points. But"''" satch out  fo
 r  the evil knight"''" because he
 is out  to get you."
9040 PRINT    Rlso  there are  tre
es  in your"  '" way  s-o you  loust  g
0  around  them."
3050 PRINT  ''  INK 5;"  PRtSS RNY
 KEY TO CONTINUE":  PRUSE   0
9060 CLS     ;  PRINT RT 2,ii;"ThiS  is
  The  castle     :    A";  PRINT TAB 23
 -                     . PRJNT TRS 23; "UltJ"
9070 PRINT      This  is  the Knig
ht           This  is  the hero
   *^* **
9080 PRINT  '"  To move  the hero
 iVOU;      use  the  cursor Keys."
9090 PRINT         '  INK 6;"   N.B.  If  th
 e  Knight  is about       to aet you
     ,? you  can  xill  hiis      t?y  p 1 Ss-B i n
 3  the   0  Key,But  be     careful yo
 ij  can only  do  this     twice."
3100 PRINT      Press any Key  to
   s   t a  r   t   .  "  :  PRUSE  0:  RETURN
3499 STOP
9500 FOR 1=144 TO 160
9510 FOR n=0 TO  7
3520 RER1> UDG:  POKE USR  fCHR$  a)
 +n.UDG.
9530 NEXT  n;  NEXT   a
 954-0 RET UKf-i
 9e>00 DRTR  0   , 24 , 60 , 126 , ^55 , 129 ^ 15
 3> ISS
9610 DRTR  0   . 0,204  , 304-,SS5. a2S  , 12
 S   ,
3620 DRTR  0  , 0 <204 / 204-, 255 / 0  , 14 ? 1
 -7
9630 DRTR 165,165.165y169,129y1^
  1    . 1
9640 DRTR 136 y 136 / 13S , 1;:;6 , 136 > 13
 S  ^ 36 y 255
 9650 DRTR 145y145y153y123y12Sy12
 S,12Sy255                                   ^
 3660 DRTR 1,1y1y1y1y1y1>255
 9670 DRTR 24,24y186y90y25y36,36y
 36
 3660 DRTR 24,24y61y90y152y35y66y
 3690 DRTR 231y153y129y66y66,36y3
  3  24
 3700 DRTR 231y2S5y25Syl26.12&y60
  50  . 2-5-
 9713 C-RTA 231 y 255 y 219y 102 y 30 , 126
 .60y24
 ^-720      12^ 129  , 255 , S5S . 129 y 25
 5y255y129
 3730 DRTR 255y129y255y129y255y12
 9y255y129
 9740 DRTR 0y24,60y126y255y255,24
 =24
 3750 DRTR 24y24y60y90y153y60y126
      . 24
 9760 DRTR 24y24y16By90y25y60y126
 y35



 Leve  I   : S                    S  c o  r e =0

                   ?       4>  ?
                         ^  A    fUU-jQ    ?4^





                         A     .



 The U.D.G.'s are  as  follows..

  R BCD EFG  H     I   U? K   L    )?}  N  O   P   Q
  ?     nr  I              9  ia g    .fr   i    -i-

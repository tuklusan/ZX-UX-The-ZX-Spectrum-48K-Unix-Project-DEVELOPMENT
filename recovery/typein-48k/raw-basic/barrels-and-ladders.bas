SCORE:O
TIME

SSJUB



           g





         1  REM
         a  REM   * BBRRELS RND LADDERS
      3  REM  * (C) D.MILLIN6T0N 1983  *
         4- REM   *  it *?  It                                t a-X-?ih *?*  f-i-it  ??
    5;
    6:
   le GO TO 1000
  100 XF RTTR  (l.XJ ;>5e. THE?  C-O  T
 O 700                                                                                    ,  ^
  10S IF INKEY$=**" THEN FOR    i =i  T
 O  30:  NEXT  i:  GO TO 300
  110 PRINT RT  l,x;"     IF bf THE
 N PRINT RT  L-lj.x;"   *?
  IIS IF  If THEN PRINT RT  l^Xj  IN
 K  l;'n":  IF bf THEN IF ftTTR  CL-fi
 .X>?:57 THEN PRINT RT  l-l,x;  INK
 1; "R"
  120 LET xlax-l-(INKEY$ = "8'*)  - CINKE
Y$="5-)
  121 IF 1=20 THEN IF xl?2S THEN
 LET X1=X
  122 IF  bf THEN IF RTTR  tl,Xl)=S
 8 THEN LET Xl=X
        <1 o'a    I pT  V =* 1
  125 IF X=-l OR Xa32 THEN LET  X =
 X-SGN          .  GO TO 700
  130 LET  lf=G.  IF RTTR
 THEN LET  tf=l
  135 XF INKEY5="0" RND  Cf THEN G
 O TO 20(C)
  136 IF RTTR    ( I  , X J =*^0 THEN GO TO
  7O0
  137 IF RTTR  (I.X)=5S THEN LET   b
 f=l:  LET m?="E-;  BEEP -0S,0;  BEE
 P  .05,4.0;  BEEP .05,40
  14.0 PRINT RT  l,x;in$;  IF  bf THEN
  PRINT RT  L~l^x;  INK 2;"D"
  14.5 BEEP .03,20-1
   14.7 IF bf THEN IF 1=20 THEN IF
 X=2S THEN GO TO  4-00
  15(C) GO TO 300
  200 LET Z=USR 320O0
  205 IF RTTR  (1-1,X)=57 THEN FOR
  i=l TO  1-4- STEP  -1:  GO TO 220
  210 IF RTTR  (l+l,X)=S7 THEN FOR
  i=l TO  1+4-
  22(C) PRINT RT i,x;m?
  S30 BEEP .02,20-i
  24.0 PRINT RT i,x;  INK
  250 NEXT      i
  260 LET  l=i;  GO TO  14.0
  3O0 DRRU  INiw^ERSE 1;  INK S;-1,0:
  LET ti=t3-l:  IF ti<=0 THEN PRIN
 T  RT 1,0; FLR5H 1;"T1ME UP":  GO
 TO 700
  305 BEEP .02/INT  (PEEK  23572.''Si
    :  LET  m  f sNOT m  f   :  IF   l?  f THEN LET
 ZsUSR 32000
  310 GO TO 90
  4.00 LET ba=ba+l:  RERD i/Z: PRIN
 T RT i,2;  INK 2;"D";fiT i-i^x;"
   : LET bf=0;  LET ?$="B"            _  ^
   4-10 DRTR 20,26,20,27,20^28,20^2
 9,20^30.20,31,19,30,19,29,19>26/
 19,27,IS,23,IS,26
   4.15 LET  S C =S C+t i  * <no ^2-3)  :  PRIN
 T  RT 0.26:  BRIGHT (C);  PRPER S;sc
   4^20 BEEP  .2,5;  BEEP .2,10:  BEEP
  i2SS    3 PLOT 4.0/163; DRRU INK  1; 160
  .0;  LET  ti=rl60.  PLOT INUERS^ 1;
 INK l;201,163
   4.30 IF ba<12 THEN GO TO 300
   4-35 PRINT RT 1,0;  PfiPER  1;  INK
 7;" WELL DONE/BLTT YOU WON'T ESCR
 PE            US NEXT TIME...",:
 PRINT
    4.4.0 FOR i=12 TO 23 STEP  2
   4.50 FOR  J=-4. TO 3: LET Z=USR 3S
 00O:  BEEP     . 1> i ?t-4.-RBS  J: NEXT   J
   4.60 NEXT     i
   4.70 FOR    i =60 TO -30 STEP -3: LE
  T Z=USR 3200O: BEEP  .04.,i: NEXT

  500 LET no=no+S
  510 GO TO 1002
700 PRINT RT          IF bf THEN
 PRINT RT  l-l/X;  INK 2;"D"
 705 RESTORE 710.- FOR     i =1 TO 10;
 PRINT OUER l;RT  l,x;  INK
 : RERO p: BEEP  .1,P:  NEXT    i
 710 DRTR 2,3,1,2,3.5,2,3,4-/3
 71S PRINT  Jt0;fiT l,la?2-l;" "2?S
;   : LET  ia=L2-i:  IF ia>a THEN UCT
 ZsUSR 3SO00-I-USR 32000^ GO TO 83
75720 PRINT INK 3;RT 2,7;"YOU GOT
   ba+6#(no-8)  ;  " BRRREL"+ GBP"S" RN
D  ba < > 1)
 725 FOR i=0 TO -50 STEP  -5:  BEE
P  .2.i;  NEXT     i
 726 PRINT RT  10,0,- BRIGHT 1;"
 PRESS RNY KEY TO PLRY RGRIN
 730 PRUSE O:  RUN             ^
1000 IF PEEK USR "a"<>129 THEN G
O SUB 9500
1001 LET   (li$ = "e**:  LET  12=3:  Lc  i   n
0=8:  LET SC=0
1002 PRPER  7;  INK  0:  BRIGHT (C):   F
LRSH  0;  OUER 0:  INUERSE 0: BORDE
R  6:  CLS     : PRINT RT 0,20; PRPER
6;  BRIGHT  1; "SCORE     S-C  /
 H7ICT.T FOP      i =B TO 21 STEP 5; PRINT
 RT     i .0:  INK  3:
                                                                                           .  nexT      i
 1004- PRINT INK  5; 0T 21,25;
          ; RT             i.NK
1005 RuSTORE  i05i5
1010 FOR J=1 TG  6
10S0 KiiRD  .x,y
1030 f-OH  1 =y  JO y-& &TEP  -X; PRI
NT RT i,x;  INK 1;"R";:  NEXT    i
104(C) NEX*T   J                                       _
1050 DRTR 7,20,22,20/12,15,27,15
 ,21,10,7,10                               ^   ^
2010 LET bf=0:  LET  IDf=l:  LET  ba =
 02O20 FOR i=1 TO  12: PRINT ?(C);"  B
 "i   ;  NEXT     i
2100 DRTR 15/1,10,29,5,1,5,GBP7
2110 FOR i=l TO  4.;  RERD W/Z
212(C) PRINT INK  2; RT  y/Z;^*DDD"
2130 NEXT     i
215(C) RESTORE 210(C)
219(C) POKE ?32004.,riD
 2200 FOR     i =0 TO no-l
 221(C) LET l=INT    ( i y (no/'4. J 5 5-5-fS:  P
 OKE 23296 +  i ?2,  I
 2220 LET X=INT  (RND*22)-*-3
 2225 IF 1=20 THEN IF X>=20 RND  X
 <=24. THEN GO TO 2220
 2230 IF RTTR     ( L  . X-1) ???RTTR    (  I  / X .1 +
 RTTR CL/X+lJOiee THEN GO TO 222
 0
 225(C) POKE 23297 + i *2,X+12S-S {X <16J
 2255 PRINT RT  l/X;  INK 4;"C"
 2260 NEXT    i                                         _
 2270 LET  lf=0;  LET  la:20:  LET X =2
 22275 IF RTTR  (L/XJ=57 THEN LET    t
  F =1
 2276 PRINT RT l/X;m$
 2280 RESTORE  4.10: FOR   a =1 TO  ba ;
  RERD P/P:  NEXT    i                       _   _
 2300 PRINT RT 1,0;"TIME:      PLO
 T  4.0/163:  DRRU INK  1; 160/0: PLOT
  INUERSE  l;  INK 1;201/153
 231(C) LET ti=160                           ^ .    .
 34.00 PRINT RT 2/11; FLRSH  l;  GET
  RERDY"
 2405 FOR     i =1 TO 15(C):  NEXT     i
 24-10 PRINT RT 2,11;"
 250O GO TO 10(C)
 95(C)e RESTORE 9510: FOR i=USR "a"
  TO USR "e"+7;  RERD X; POKE i/X:
  NEXT     i
 9510 DRTR 129/129/255., 129/129/12
  9   , 255 , 129 , 60 / 60 , 24., 126 , 153 , 24-, 36
 ,66,102,6(C),126/153,255,60,3B,195
 ,6(C).S6,255,129,255,129,66,60,1S9
     , 189 / 90  / 60 , 24., 24., 36  , 66
 9515 FOR 1^32000 TO 32150; RERD
 X:  POKE i,X;  NEXT     i
 9520 DRTR 33,0,91/6/8/197,62/22/
 215/126/79/35/215/126/230/31/215
 ,62/16,215
 953(C) DRTR 62/0/215/62/32/203/118
  /4.0/ 16/62/ 16/215/62/ 1/215/62/ 14-4.
 ,203/182/215
 954.0 DRTR 126 , 230 , 128, 7   , 254., 1, 4-0
 /2,62,255,87,126,23(C),31,13(C)/95,7
 l/2(C)5/130/125
 9550 DRTR 254-/60/32/3,123/130/95
    , 67 , 205 / 130 / 125 , 254- , 57 , 32 , 2   , 203 /
 24-6, 123, 130,71
 956(C) DRTR 205 , 130, 125 , 254., 58 , 4.0 /
 11/ 123/254./(C) / 4.0 / 6/254./31/40/2/S4-
 /4/126.238
 9570 DRTR 128/119/126/230/192/17
 9, 119 .62/22/215/ 121./ai.5/ 126/230/
 31,215,62/16/215/62
 958(C) DRTR 4,215/62/146,215,35/19
 3/ 16/ 1.32/^ 2(C)3./229/ 197/ 121/15/ 15/ 1
 5/79,230,224/168
 9590 DRTR 111,121,230/3/238/88/1
 03.. 126 / 193 . 225 / 201
 960(C) RETURN

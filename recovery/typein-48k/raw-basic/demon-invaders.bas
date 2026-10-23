54. PRINT INK  5; BRIGHT i;AT 16
 , 17; "o.    o    o??
  55 PRINT INK  5; BRIGHT a;flT IB

  56 PRINT INK   4-; BRIGHT 1; RT 17
          PRINT INK  3; BRIGHT 1;
Hi 17,19;"b,"
  58 PRINT INK  S; BRIGHT 1; PLRS
H 1;RT 16,26; "GBP3"; PRINT INK  4-;  B
RIGHT 1; FLR5H i;BT                                     I
?NK S; RT 16,30; "O"
  53 PRINT INK 3; BRIGHT  1:  FLfi6
M 1;  ; RT 13,; "O" ; prinr  jl'nk  5;
BRIGHT  l; PLRSH l;RT 18,28;"D";
INH  7; BRIGHT 1;RT 18,30;"Q"
  70 INK  5; BRIGHT  1; PLOT 0,50;
 DRRW 255,0
  71 INK  S.  23RIGWT  1. PLOT 200,1
4.;  DRRU e.,3S
  38 INK  3.  f^LLfT  0,ILS.       255/
0
 120 INK  7.  BRIGHT  1: PLOT 0,0:
DRRU 0,175:  DRRU 255,0; DRRU 0,-
175;  DRfiW -2S5^0
 125 PRINT RT K,l-1;"    "
 126 PRINT ?T X,t-fl;"   "
 127 PRINT RT X-1  .  I  ;  "    "
 128 PRINT RT K+l,l;"    "
 130 IF INKEV$="(C)"  RNGBP>     t <29 THEN
 LET l=L+l
  14.0 IF INKEV$~"5*' RND     I >2 THEN
LET  Lal-1
 150 IF INKEY^ss-e" RNO X<13 THEN
 LET X=K+1
 160 IF INKEY$="7" RND K>2 THEN
LET X-K-1
 180 PRINT RT INT TO,INT m"   "
 200 PRINT RT K,t-1;"-*-
 210 PRINT RT x-i,i;";"
 220 PRINT RT  X-?-l,l;"J"
 230 PRINT RT fc,l+l;"-'*
 24.0 IF INKEYS = "0" THEN F'OR    f =^0
TO 10; BEEP .005,1     NE.XT  f:  Tr
  K =:INT   Jft RND    I sINT  n THEN GO SUB
 1000
 24.5 LET n=n+INT  (RND?3.>-1
 24-6 IF r)<3 THEN LET nsn-J-1
 24.7 IF  n.'?29 THEN LET naH-l
 24.8 BEEP .01,10
 250 LET fl)=?+0-2
 252 IF score>1000 THEN LET ?=?+
0.2;  IF  l?.>P000 THEN LET JB=?+0-P
 255 IF n<l OR n>31 THEN PLOT  GBP?,
0; DRRU 0,175: DRRU 255,0; DRRU
0,-175: DRRU -255,0
 260 IF B>1S THEN GO SUB 2000^
 30(C) INK  4-: PRINT RT INT  ?  , INT  n
 ;               :  INK   7                                         ...
 310 PRINT RT l,l;"EOKE  = ";sco
^l99 GO TO 125
1020 PRINT RT          PRINT    ,  O
UER  l;flT  k,L;"rS*'            ^            ^
1030 FOR  f=l TO 12; BEEP  .l./20+f
  :  BEEP .1,-4:  NEXT    f
104.0 PRINT RT k,W  _  "
1050 LET ?=3; LET nsINT  (PND?2(C)*
 ?i-3
5;
4.020 INK 5; BRIGHT  1; PRINT     ; PR
INT "You are  in  the gunning pod
on   a  secret aission,you are aboa
rd   a  rebel  cruiser and Just  as   y
ou   enter your saiaxv you are
     attacXed  by dehon inurders"
4-030 INK 5: BRIGHT 1; PRINT     ;  PR
INT     :  PRINT   "      5   =  LEFT".- PRINT
  ;  PRINT   "     S   = RIGHT"; PRINT     :
RINT    ??     6   = DOUN";  PRINT     ; PRINT
         7   =  UP"; PRINT      .  PRXX-/T   "      0
 = FIRE"
4-035 PRINT INK  3} BRIGHT 1; RT B,
0;
    *       "
4.04.0 PRINT INK  6;  BRIGHT 1;RT Si
,l;"HOPE YOU GET  R GOOD SCORE":
PRINT INK  6;  BRIGHT-JjRT 20,1;   F
LRSH 1;"PRESS RNY KEY TO STRRT^:
 FLRSH   0
4.04-1 INK  4-: BRIGHT 1; PLOT  11.5^,5
0;  DRRU 70,0; DRRW -10,10; PLOT
115,50:  DRRU 10,10; PLOT 155^60:
 DRRU 50,0
4-04-2 INK  4-; BRIGHT  1: PLOT 130,5
0:  DRRU 10,10; PLOT 170,60; DRRW
 -10,10:  PLOT 138,70; DRRU 24,0
4.04-3 INK  4-: BRIGHT 1; PLOT 120,3
0; DRRU 10,20; PLOT 180,30: DRRW
 -10,20
4-04-5 PRUSE 9999
4-04-9 REH STRRS
4-050 BORDER 0; PRPER 0;  INK  6;   C-
LS   FOR n=0 TO 50: BEEP 0.005,4-
0+2:  BEEP .005,20;  INK  7; BRIGHT
  1:  PLOT INT  (RND?25&)+5,INT  (RN
D?120^ +50; NEXT n;  INK  4.; GO TO
S
5000 REH USER DEFINED GRRPHICS
5001 DRTR 0,24., 126,255,24-, 36, 0,0
5003 DRTR BIN 11111111,BIN 11111
111,BIN 11000000,BXN 11111111,BI
N 00000011,BIN 00000011,BIN 1111
1111,BIN 11111111
5004. DRTR BIN 01111111,BIN 01111
111,BIN 01100000,BIN 01100000,BI
N 011000^0,BIN 011000TO,BIN 0111
1111,BIN 01111111
5005 DRTR BIN 01111111,SIN Ollli
111,BIN 01100011,BIN 01100011,BI
N 01100011,BIN 01100011,BIN 0111
1111,BIN 01111111
5006 DRTR BIN 01111111,BIN 01100
001,BIN 01100001,BIN 01111111,BI
N 01111000,BIN 01101000,BIN 0110
0100,BIN 01100011
5007 DRTR BIN 01111111,BIN 01100
000,BIN 01100000,BIN 01111100,BI
N 01111100,BIN 01100000,BIN 0110
0000,BIN 11111111
5000 DRTR BIN 10010101,SIN O0001
001,BIN 10100100,BIN 01001010,BI
N 10O00101,BIN 10000111,BIN 1001
0010,BIN 10010101
5009 DRTR 195,219,255,102,126,12
6,S6,107,195,219,255,102,126,126
 , 106, 214., 0,219, 219, 255,231  , 125, 1
02 ^ 1S6 , 16 / 1&./ S6, 56 / iOS , 10S , SS4. y S
  4.5010 FOR  n=14-4. TO  154-
 5011 FOR  fss0 TO  7
 5012 READ a: POKE USR CHR*
    ^ a
 5013 NEXT    f
 5014 NEXT  n
  504-0 RETURN
 699S REH YOUR OERD
 7000 BEEP 0.5/-2: BEEP .2,-2: BE
 EP .3>0                                           ^
 7010 PRINT INK  6; BRIGHT I;RT 1,
 1;"THEY HflUE DEFERTED YOUR CRUIS
 ER THEY ARE NOU BUILDING THEIR
    STRONGHOLD"
 7025 PRUSE 100
  7030 INK 2: PRINT ?T

 7035 BEEP .2/-2
  i704.S040 PRINTBEEP  .2,-4-INK 2;RT 9,6;"
 705^ PRINT INK SjRT 10,5; sBwrn

  7060 PRIf^ INK  4.;RT ll.S;

  706S BEEF .5,-7




       Calendar
                                         This program has b
       on Aquarius               on the ZX81, Spectr





10 REM CRLENDER FOR THE
    UN^XPfllfiED flOURRIUS
20 REM WRITTEN BY M.J.Dyos
25 PRINT CHR$  (li)
30 PRINT TflB  (15)i"GRLENDER"
40 PRINT TAB  (155j"========"
45 LET s4 = "
 S0 INPUT "ENTER YEAR-? "iY
 60 REM >>>checK that year has
been  typed  in correctLy<<<
 70  IF YoINT  (Y) THEN GO TO 5(C)
 80 IF Y<1 THEN GO TO 5(C)
 90 IF Y>5000 THEN GO TO 5(C)
100 REM >>>find  first of  \Jan< < <
110 LET Y1 =INT  ((Y-l)yl00J
120 LET Y2=Y-1-100*Y1
130 LET D=7Q9+YS+INT  (Y3/4)+INT
 ?Ylx4) -S^Yl
140 LET  D = -(0-(INT  (Dy'T) *7)  )
150 PRINT CHR$  (11)
160 PRINT TAB  <15) ;Y
170 PRINT TAB  {16);"===="
180 PRINT
190 LET L=0
200 REM >>checK  for  leap ycar-t^
210 IF      (  f INT  iYi^4) i4) <>Y)    } HEN
    GO TO 250
220 IF     ( (INT             i4-S!0) =:y) TH
     EN GO TO 240
230 IF      i (INT  (Y/100> *100)=Y) TH
     cN GO TO 250
240 LET  L = 1
7070 PmuiSk
     707S^ BEEP .5 /-9
    7140 FLASH 1: PRINT RT
     TOTRL SCORE  =   score:  FLRSH 0.
     7500''cLS   FOR F?0 TO 30: BEEP  ?
     01,10+F; BEEP
    PRINT RT 0,0;  INK  6; BRIGHT 1,  Y
     OU HflUE SRUED YOUR
     OU CRN COMPLETE   YOUR MISSION   -
      WELL DONE": FOR     TO g_STEP__
      -1;  BEEP  .01,10-l-F: BEEP .02,20-<-
     760i^INPLrF "ANOTHER GAME 7    LI
     7ll0*lF AS="Y'* OR fl*="y" THEN BE
     7620^iF^A*="N" OR A?="n" THEN BE
     EP 1^0: BEEP  .5,-5: BE^
      PRINT FLRSH  1;  INK 6;RT 10,10/
     BYE     ,  BYE"

                 Demon Inyaders
                    by Alan Price





  been designed to work   Aquarius. It is fully error-trapped and takes
 rum or the unexpanded    into account leap years in its calculations.





   300 PRINT   "
    >  ;
   310 PRINT   "     SUN MON TUE  U?Ef>
  THU FRI SRT"
   320 PRINT
   330 IF N<>2 THEN GO TO 350
   340 LET M (2) =M (2) -i-L
   350 FOR 1=1 TO  S
   3S0 PRINT
   370 FOR   J = 1 TO  7
   3se LET D=D+i                      ^
   3Q0 IF D>M(N) THEN GO TO  4  ?0
   400 IF D<=0 THEN GO TO 430
   410 PRINT TRB  (J*4);D;
    430 NEXT    J
   440 LET  v.??l
   450 IF D=M(N) THEN GO TO 47(C)
   4&0 NEXT    I
   470 LET D=l-J
    4S0 IF INKEY$="" THEN GO TO 4S3
   490 PRINT    :  PRINT    : PRINT
   500 KJFyT  N
   1000    , ss , "MRRGH****'   , 31 i  HPRILa^a^
   ieie^gsTfi                                     J. 30 ^ " ._?Ul_Y i         i  i  #31^  HwL*L.-o?i*
H  1020'^DRTR "SEPTEMBER" ,30. "OCTOBE   R*t" >31., "NOVEMBER*" ^30, "DElEMBER
     *  ,31

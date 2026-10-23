S  LET bS=0
  10 PRPER  0   :  Ci_S     ;  BORDER   0
  20 Pi-PSH  0.  OVER  O;  INVERSE   S-
  30 BRIGHT  0
  3S PRZ.NT PT 10^0; PLRSH  Ij
   4.  . "STOP THE TRPE    -  PRESS BNY
V    ?           :  PRU5E  (C);  CL.&
                          xtJ*--   a.;            inik
RRPE~r"   '    ' "PC'T *?. P-K ZX Sp e ^  t   UiiiII^  ?. tSjj     a u i     .?)       y  i f}.GBP     '  "   ' " WS' VjS  -C"^ f" i
5  the  ca-pe't  layer
  ffiszs  laying  the  ouee.nsRed     P-
 t  , 3''i      is  3 bout  to    tdke
first steps into  the   stars-One
  P r o b I e in ; T h e  carpet   a r> d j  t a r s  h 3 v
GBP borgiar alarms and    if Chns
touches  them  hs  will    be destro
yed . use ;       z -t-e ft     x -Hi      t      '  GBP-Down    f-Up    "Press     s    to sta
 r    t ??A5 PRUSE 600                                                           .
_  4.& IF INKEY$<>"S" THEN GO TO   4.

  S0 RESTORE
  70 PGR f=USR  "a" TO USR
  80        a;  POKE


  :IS'0 LET  S -0
  1^121 PRINT     ;  PRINT    ;  PRINT INK     =.5

        ***###***   *  if********* **
  ** **                        #    *    *
  ** **********   *   *    *  ************
       if- *

     ^  *
   *        .v .f    ^      ;t  A-                          i       i   A- a A ii- *  s- *   * * * *
***          *                                                  *
  ** **   *******    *****^-**
  ** *#                        #          *
      *          *  *****   *   *    *  ******   #
  *******                    *           ****
??**      ******************
    ****   *                                    *  ****
   X- *

 130 PRINT INK  S;  ?? **********
        ***********
                 ***************
********************
 14.0 LET a=lS;  LET   b = 10
 145 LET e=-l;  LET  f=0
 150 PRINT RT  a., b;  INK  7.;-R*
 a&0 SEEP .01,0: BEEP  ,31,1:  BEE
P  .01,2;  BEEP  .01,3:  BEEP  .01..4-:
 BEEP  .01.5;  BEEP  -Ol.-B:  BEEP  -0
1     . 7
 17(C) IP INKEV$="2" THEN LET e=-l
  LET     f =0
 180 IP INKEY$="X" THEN LET  fisl:
 190 ip^INKEY$="C" THEN LET  f=l:
 LET   e =0
 200 IP INKEY$="f" THEN LET
  LET e=0                                _
 210 PRINT RT a,b;  INK  2;
 223  IP 5CREEN5   Ca-i-i   .. b+e > =''*" TH
EN  G!0 TO 2S0
 225 IP RTTR    ( a+f,b+e) =BIN 00000
010 THEN GO TO 250                       ^
 230 LET  S=S-fl;  LET a=a+f:  LET  b
 ~235 PRINT RT 0,0;  INK  7;  INUERS
E  1; "SCQRE = **; s;  ?? HI = -;hs
  24.0 GO TO 150                                                   ,
 350 PRINT RT  a + f^b+e;  PLR^H  1..
INK  6;  PRPER         POR  f=1 TO  ^
0:  BEEP .01,5:  NEXT  f:  BEEP .1^1
0;  BEEF .01,10
 260 IP s>hs THEN GO TO
 270 CJRINT RT 21 ,-S; " IJ^'S  t         Ofi'S
  <y./n>      INPUT a$:  IP a$ = "y      t
HEN CLS     :  GO TO  4.0
 290 GO TO 10O       Continued on p8ge 35
300 CLS     :  PrtPER  6:  CLS
       3   i B  JNK   0
   330 PRINT  f)T  1^3;




    34-0 PRINT AT 17,1;"n    I r.
      "  ??;bs
   350 PRINT AT 19,1; "1

   360 FOR  ?=1 TO 250:  NE.XT     f
   370 PRINT RT 17,1;" EW
                                    The  keyboard  is scan
    Screen Colour          second by the  interrup
        on Vic20               197 on the zero page w
 is program  enables  the  use  of  the   values depending on th
nction keys to change the screen/border  The relation between th
 lour combinations.                      address  and  the  key
  , Decrements the contents of (36879).     follows:
  .  Increments the contents of (36879).     Function  1 = 39
  . This resets the screen/border colour   Function  3 = 47
   to white/blue.                           Function  5 = 55
he program works in the following way.     Control branches to th
f'CR     r       rcf  sc.;  RRlNT ?7
   f}S:  BEEP s^S.f: PRINT ?T
      ?  '?   "  ? NEXT    f
   390 FOR  f=Sl TO IS STEP  -1; PRJ
  NT PT  r,GBPS;s:  BEEP .05,f; PRINT
  PT f,SS;"      ":  NEXT    f
    4.00 FOR fa2S TO  14- STEP  -1:  PRI
  NT RT aS,f+3;"  '^RT is,f;s;  BEEP
    .05,f; NEXT    f
    4-10 PRINT RT lS,a4.;s;"
    4.12 FLASH 0: PRPER 0:  INK   7
    4-20 LET hS=GBP:  GO ID
  1000 DPTR  24., 24-, 125, 24,24., G(C), 3(C) .
  36
  1010 DRTR  153,. 90,50,255,255.. &0, 9
   0, 153


                     Red Carpet
                         by Gavin Devine

nned every  1/60th   routines consecutively. At each routine the
pt  routine; location   ?contents of 197 are checked against the
will contain different   values for the appropriate function key.  If
 e last key pressed.   they tallythe contents of (36879) are either
 he contents of this   incremented/decremented, or loaded with
   pressed  are  as   27, which resets the border/screen colour
                         to normal.
                         Control then branches to (60095), and
                      the process is repeated.
                   To start the routine: SYS 673.
hree separate sub     To stop: run/stop restore.

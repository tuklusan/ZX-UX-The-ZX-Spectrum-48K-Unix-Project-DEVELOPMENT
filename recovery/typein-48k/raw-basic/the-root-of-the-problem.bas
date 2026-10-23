,                     (
RDROTIC";  LET D* GBP2) ="CUBIC'*; LET
 DS (3.1 ="OUfl.RTIC" : DIM              L
ET R$C1J="  Real     "  ; LET R? {2> =
 Ccaple.v   ??
  1 pft LET Cs=  Pres5   iacUdB" ^
 ^130 PRINT-  ...AT 9,10;A*:-   .  _.     PRINT  err
          _         ?lF"AKfeYi=CHR,IS^S;  iiia PAUSE
13 THEN GO TO 155
 ill CLS^? PRINT     This Progra
m is designed  for  thaso lution of
 Ouartic^ cubic  ansi                         c
quations.   As you mayweil Kno?>a
 Cgebraic equations ofdegrae  Less
  than   5  can  be ioLvedby farsolas
 Without recourse  to  nufia.-icsl      i
 teraiion.":  PRir-fT hT =b,3;C5
 -3.58 IF INKEY*=CHA? 13 THEN GO T
 t? 1d0
  IS(C)  GBP50 TO 158
  160 CLS
  165 PRINT AT 10,0;"Enter Hignes
   t Power  of Equation:
 2/3 or  4-"
  170 INPUT  N

 180 IF N=2 THEN GO SUB 300
 200^?2 IF N=4. THENTHEN GOGO SUBSUB 530@00
C TD iLS'-"*                         ?
 255 IF N=4 THEN GO SUB 1100: GO
 TO 2000
 300 AE?
 301 ?EW OL'ADRATIC PROGRAM
 302 RGBPn
 305 CLS      .  PRINT   "
                                                                                                                             ?j O 50 tve           S
  + Ba  + C = D                _   AX
 309   r iH R12,2}   ; DIM  C (IS)
 310 INPUT  ??A^-;Ct3)
 312 INPUT  ??fi'=-;Ct2J
  314. INPUT  ??C = ";Ctl3
 320 LET H=C13J; LET BsC IS}   :  LET
 C=C flJ
 330 LET  S =BS-B-4.*A*C;  IF O<0 THE
N  GO TO 380
 360 LET A (1, 1) ? (-B+SOR 0> ^ (Sf-Pi)
 370 LET  A (2/1> = !-B-&OR 03   (2*A.>
  GO TO  4.00
 380 LET Afl/1)=-e^(2#A>:  LET  fit
2/1)=A{1,13
 390 LET A(l,2)=SOR
LET Af2,2)=-Afl,2)
  4.00 RETURN
 500 REM
 501 REH CUBIC PROGRAM
 502 flGBPH
 505 CLS     ;  PRINT   "
             I? To solve      &
         3                         Ax     +
B B B
 535 IF  As=0 THEN PRINT     ?=?  P
lease re-enter    S  ^you have   a  qu
sdrstic":  GO TO 165                  _
 536 IF D=0 THEN PRINT     Da?  P
lease re-enter     2  ,you havea qoa
dratic  an?f one root  is  zero**.-  GO
 TO 165
 54^ LET 01s0?0?-04-R?R:  LET Tsl/*?
 550 IF Ol<0 THEM GO TO 650
 560 LET  S4.=R-i-SOR Ol;  IF S4.<0 TH
EN LET SI =-CABS S4.tT)   ;  GO TO 5(C)0
 570 LET Sl=S4.tT
 5S0 LET S3=R-SOR Ql:  IF S3<0 TH
EN LET S2=-(AeS S3tT3:  GO TO 600
 590 LET S2=S3*T
 600 LET Xl= (S1+S2-BJ -.'ft
 (C)10 IF (C)1>0 THEN GO TO 630
 620 LET X2a?(&+R+T> XA; LET X3^=X
2;  GO TO 73(C)
 630 LET Es> (Sl-<'S2-f2<-B3(2?A>
  64.0 LET F= (S1-S2J *SOH  {33 y'ta*?3
 ;  GO TO 74.0
 651 LET M5=l
 652 IF R<0 THEN LET MS=-1
 570 LET OS=ABS Q: LET
R  COSt33
 680 LET H=ACS  G
 690 LET H1=HS?2?50R  (-03:  LET   J
sHli'COS  (H^33
 700 LET XlastJ-BJv'A
 710 LET U=Hl*COS  (H/S-fS^PI/S)   :
LET  X2=: (J-B3 y-R
 720 LET J=Hl*CO&  (H./3+4.*PI/3>   ;
LET X3=(U-B3/A
 730 LET Ari/13=Xl: LET A(2,i3=X
2;  LET A(3,13=X3:  GO TO 790
  74.0 IF F<0 THEN LET  F = -F
 750 LET A(1/13=X1;  LET R(2,l>s:E
  LET A(2,23 =F
 760 LET A(3,13 sA<2, 13  : LET R(3,
23 s-A(2/23
 790 RETURN
 800 REH
 801 REH OUARTIC PROGRAM
 802 REM
 80S CLS     ;  PRINT   "
                   TO solve"
 506 PRINT ??4-3            2
               Ax       *? BX     *  CX      *?
DX   +   E    =  0"
 507 PRINT    ??

 809 DIM U(4.,23:  DIM  Z (S)  :  DIM A
 (3,23   :  DIM  C (4-3
 810 INPUT "A = -*;Z(S3
 S12 INPUT   ??B = ";Z(4.3
 813 INPUT    ??C  = ";Z(33
  814. INPUT "D = ";Z(23
 815 INPUT       Z(l)
 620 LET RM=Z (4-3 yZ (S3   .  LET RN=Z  (
3.<./'Z(S3; LET RD=Z (23    (53   :  LET  R
0=Z (13 yZ(53
 830 LET N=3:  LET CC4.3=e: LET C(
 33 s-4.?RN; LET  C (S3      ? (RM?RD-4.?RO
84.0 FOR J=1 TO  3
 Hi LET pi=RM*RM/-4.+2*Y3Li-Rr4
 ill                        AND P
S>=0 THEN LET U=SOR PI: LET UsSO
R  PS:  GO TO  BS-7
 85S NEXT    I
 85B GO TO 900
 its Ei? glf:=LET a.R?.a-U. LHT
 ^|?0'"f6r''i?!''to''|? t-ET X?i):  LET uCI,a)=?tr,2>:  NEXT  I
 375 DIM R(2,2)                            ^
 aae let  fl=l;  let B-RM/2+U;  LET
C=Y1-U;  GO SUB 330
 885 FOR  1 =1 TO  2:        'it?'
         LET UCI+2^2>: NEX
 T      I
 866 LET M=0
  ail iF^u^i^aToo then let  m=j-i+i
  B9& NEXT   I
  897 GO TO 950                        ^
  900 PRINT  '"Pieasa rescaie x,  n
 unbers  too   difficult  to hanote
  910 PRINT  "fiiso  checK  if yoor   e
 quation  can  be reduced  to  a  lowe
  r  degree"
  920 GO TO S000
  950 RETURN
 100(C) LET M=0
 1013 IF'^fl^ltsT?>0 THEN LET M=M+1
 101! If'^<1 THEN LET M=l;  .IF M>2
  THEN LET M=2
 1020 PRINT "where;"   _
 1030 IP N=2 THEN PRINT   R=^C<3
 )."B=";C(2?: PRINT
 1032 IF N=3 THEN       /"?="; Ct4-  J , "B ="; C (3)  : PRINT  ??C= ;C(S>/ D-
 a040^IF N=2 OR  (N=3 RNO      ^THE N PRINT '"has "'N;R5<M);  root^s; 104.2 IF  (N=3 RND M=2) THEN PRINT
  '"has  1 Real and  s  cowpiax root
 104.5 IF  tN=2 RND M= l)  OR  (N=3 RN
  !> M=li THEN GO TO 1070


  EAT YOUR HEART OUT GEORGE LUCAS!
  ASSASSIN SOFTWARE
         (in collaboration with Buccaneer)
                   Presents
in  versions  for  the 16K or 48K Spectrums
featuring conflict, gambling and The Unge. Plus
 game map and rules for Board Game option

   THE FIRST MULTI-PLAYER
     ADVENTURE GAME
 USURPER
1-10 (48K) or 1-4 (16K) players wade through the
gamut of Beasts. Men and Monsters! Amass your
forces and wealth. Seek the aid of powers temporal
and spiritual (but beware the Undead). Attack and
weaken the other players   If you get the chance.
When you are strong enough the time comes to
   overthrow the King or be crushed by his Army!
           The first part of a trilogy.

GBP6.50 P&P incl.
1050 IF  (N3s2 RND MsS) THEN PRINT
   '"Xla">R(lyl)>"+    i  "iRBS R(1/2)
  10S2 IF  (N=3  RI^D Haa) THEN PRINT
    '"Xls!"'R(l  1)
  1060 PRINT '"x2=";Rt2#1)^-    i
  RBS R(2.2)
  1062 IF N=3 RND M=2 THEN PRIITT
   ??X3 = "; R f3, 1)  , "+  a  ".-RBS fl(3,23
  1065 RETURN                                      , ^
  1070 PRINT       ' "Xle";R 11, 2> ? "xSs-  ?fl
  1072 IF  (Na3 RND M=l) THEN TOINT
                 ' "X3=:"; R (3/1)
  1075 RETURN
  1100 PRINT "Where;"            ?
  1105 PRINT     ' "R=*'; 2 <S)  , "B=   ; Z C^)  :
   PRINT ?'C-";Z 13)  f "D.-="; 2 12)  ; PRIN
   T  "E = ";Z(1)
  1110 IF M?0 THEN PRINT        ' 'has  4.    r
     s a  I  roots r "?                  _
  1115 IF M=2 THEN PRINT   " 'i^as  "2    r
  eal and  S  coapiex roots:
  1120 IF M=4. THEN PRINT  "has   4.   c
  omplex roots:"
  112s IF M=0 THEN PRINT  "xi=";u(
  1,1)/"xs=";U(2/1):  PRINT  'x3="; u
   (3/1)  / "X4. = "; U (4./1)                        ^
  1130 IF M=a  P)ND U{4.,a)<>0 THEN  P
  RINT       ' "xl="; U (1/ 1)  . ??X2 = "; W (2, 1)  :
   PRINT      ' "X3 = "; W(3, 1)  / "-f  a       ; RBS
  U(3,2).  PRINT  ??X4^= "; W (4.. 1)  / " -   1
   "jflBS U(4.,2)                       _             ^
  1135 IF M=S HND- Wf2,2) < >0 THEN  P
  RINT       ' "Xl = "; U (3, 1)  /  X2=
   PRINT       ' "X3 = "; U lly 1)  ,   +   a
  W(l,2): PRINT "X4.="; U (2 ^ 1)  ,    -   *
   "; RBS U (2/2)
  1136 IF  M=4- THEN PRINT  '"Xl = ";UK
  1,1)/"+  a  "jflBS UCl/S):  PRJNT "X
    2 = "; U (2/1)  / " -   a  ";RBS
  INT "X3="; U(3/1) / ?;+ a  "/.RBS "52^
   2);  PRINT  "X4. ="; U (4., 1)  /   -  a      / RB
     6  U (4-/2)
   114-0 RETURN                                                         .  - .L.
  2000 PRINT RT 20/2; -DO  you
   to  cont-inue ?ath";RT 21/11/D*<N
  2010 IF INKEY$ = "V" OR IMKE^'*=*'y"
   THEN GO TO 180+(N-2)?10
  2020 IF INKEY#="N" OR INKSY$=  n
   THEN GO TO 16(C)
  2030 GO TO 2010


SPECTRUM
RAM UPGRADE A
16K-^48K





EASY TO FIT.        INCL.    ISSUE TWO
CHIPS JUST                MACHINES ONLY
PLUG IN.                    (BLUE KEYS)
NO SOLDERING.    P.&P.                                 S.A.E.for details,SENT WITHIN 10
                                        please.
DAYS

     DISPLAY INSTRUCTION SHEET
   Get the best possible results from your Spectrum.
   Deals with yellowish white, wobbling colours etc.
   Send GBP1 plusStamped Addressed Envelope

   MAIL ORDERS ONLY. Cheques/P Os to:
   FOUNTAIN COMPUTERS LIMITED
   Bishops Court,
    Bi h      t k           SORRY NO OVERSEAS

|  p                   )
 iis PRINT DUER l;RT  p r.. g  ; b* (1)  ;
IT  p r+1, g; bS (2)  : RETURN
 ISO PLOT  (g*e.> +7, M2Sl-e)  - (pr#(C).*
1-8;  DRRIJ 0,16;  RETURN
 160 PLOT  (q                 ( (2S?8)  - Jpf *(C))
 -3;  DPftUi                              I
 300 LET  g=g-f-l
 305 LET no=CODE n$(l)-67;  LET  P
 ? =no *-3
 510 LET no=noi-2
 315 IF            RND n?Cl><"P"
"HEN GO TD 225
 220 LET no=no-l                          _
 GBP25 IF n?(l)="R" OR                T
^EN LET no =ni?+2
 .935 IF n?(2)="l" THEN LET no=no
rlS:  LET pr=pr+7
 SiO IF N$(2)="F" OR n*(S)a"F"  T
-:=N LET no=no-l
 24.5 IF N$(2.^="S" OR n?(3Ja"S"  T
tcN let nossno+1
  = 5(C) LET  p?-= (2B-pr) ..'2
 250 IF pj-=INT pr THEN CO SUB  (1
"stI'^IF not pr =INT pr THEN GO SU
3  (10O*9O)
 274 IF n>=l THEN GO TO 28(C)
 375  IF no<10 THEN GO SUB 150
 277 IF no>9 THEN GO SUB 160
 S76 IF na.(C)S5 RND nod(C) THEN DR
   3,-3
 279  IF nss.025 AND n059 THEN DRR
 SSO'BEEP n,no
 290 RETURN
 999 REN
i000 FOR a=104 TO 135 STEP  6;  PL
 -iT 0,3:  DRAU 255,0:  NE>:T  a
-1010 PLOT 6^111;  DRRU -6^0^ -PI:
r'RRU 6,24,.75:  DRRU -2,0^PI;  DRR
     ' 0,-32;  DRRU -3/0^-PI
iiii RiM'^^BBroBBS
3000 LET OS0;  DIM d(30);  DIM 0?t
 ?0,1   ;  GO SUB 1O00
2010 PRINT RT O,0;"You  can now  w
,-ite your own mosicusing quavers
   (O.I   , c ro Che ts  (C) ^ minims  (N)  an
 d ^emibreves  (S3 .".;AT 13..(C);"    Y
    then  type  in  the pitch o/tha
 'lOte ie.Clsnote  C one octaveabov
 GBP middle C"
2015 PRINT "YOU may have   a  sharp
  or  flat     using   s  or  F  respect
 iveiy after  the note eg.-ciF"."
3020 INPUT "No.  OF notes  in  tune
  (up  to  30> "Md):  IF t(l)>30 T
MEN GO TO 2020
3105 FOR S=1 TO  t(l)
2110 INPUT "Leng th  , no te   i$,nS;
 IF n$=""  OR  L$a"" THEN GO TO Sll

3111 IF  l$="0" THEN LET d(S)=.02
 5:  LET go=0;  GO TD 2119
3112 IF  l$="C" THEN LET d(S)B.25
  ;  LET go=0;  GO TO 2119
2113 IF  l$="M" THEN LET d<S>a.75
  - LET go=5;  GO TO 2119
 3114 IF  L$="S" THEN LET d(S)=2:
 -ET goaS;  GO TO 2119
3115 GO TO 2110
 3119 LET nS=riH-"
 3120 LET OS((s*3)-1>=n*t1):  LET
 o $  ( (s *3) -2) =nS (2J  :  LET oS(3?3)=n
 $ (3)  ;  LET n=d fS)
3125 GO SUB 200
 2130 LET^asl:  CL5   GO SUB 1000
3135 FOR S=1 TO t(1)
 "3900 PRINT RT  21..3;  FLRSM  1; "Pre
 ii any  Key  to continue"
K:  BEEP .007,30-K:  NEXT  X
d.015 PRINT  -'''"is obtained  by     t
he               Short routine:-"
4016 PRINT    "  FOR K=-30 TO 40:  BE
EP  .007^k:  BEEP .007.30-H;  NEXT
K "
4017 GO SUB 3900
4.016 CLS     ; PRINT RT  0..0;"  Rnoth
er idea  is putting   tiiio    B'eep   s   t
atements  together eg.";  pruse 3Q
4020 FOR  Ksi TO 20;  PAUSE  5;  BEE
P  .007.5;  BEEP .007^30;  NEXT  K
4022 PRINT       '    '   FOR K=1 TO 20:  PR
USE  5:  BEEP .007,5;  BEEP .007,30
  :  NEXT  K"
4024 PRINT      This produces   3
hind  or" Munch sound  .The  two  bee
PS  can  be      taken out or  the   F
or-Next  loop   and used  in   a  prog
ram "
4026 PRINT ?'?'"Try experimentin
3  with  the  beep statefsent  ..if ap
ropriate use For-Next  loops."
4.028 GO SUB 3900
4030 GO TO 600(C)
5999 STOP
O000 CLS      :  PRINT AT 0,11;"MUSIC"
eO05 PRINT AT 1,11;
5010 PRINT RT  4,6.; "1 LERRN MUSIC

SOIS PRINT AT 6,6;"2 URITE MUSIC
6020 PRINT AT 8,6;"3 MUSIC FOR G
J^MES"
6025 PRINT RT 10,6;"4 SAVE MUSIC
6030 PRINT AT ia,6;"5 LOAD MUSIC

O035 PRINT AT 14,6;"6 OUIT PROGR
904.0'?  PRINT AT 17,7; "INPUT NO. 11-
5)  "
9045 LET I?=INKEY?
90SO IF IS="1" THEN CLS     ;  GO TO
3000
90SS  IF I?="a" THEN CLS     :  GO TO
3000
3060  IF 1?="3" THEN CLS     :  GO TO
 4.000
S065 IF IS="4" THEN SAUE "Mu" DR
TA  d  (.1  ;  SAUE "Mu2" DATA 0$0:  SR
UE "MU3" DATA      t  O     ;  GO TO 60(C)(C)
9070 IF I*="5" THEN INK  5; LOAD
"Mu" DATA d():  LORD "Mu2" DATA  O
$():  LORD "MU3" DATA  t();  INK  0:
 GO TO 2130
9075 IF 1S="6" THEN INPUT ""Y"  T
 O NEW";US:  IF US?"Y" THEN NEW
 310(C) GO TO 90AO
9979 REM
9960 DATA "C"  "D"^ "E"  , "F"^ "O" "A
1"^"Bl"^"Cl"
9961 DRTR "S"
9969 STOP
 9990 RESTORE 9990; FOR 2=1 TO 6;
  READ ZS; FOR .X=0 TO  7; READ  C;
POKE USR Z$+X,. C; NEXT X; NEXT Z;
 RESTORE     ;  RETURN
9991 DATA  "a "  , 0, 30.. 62 , 126,1S4.,56
 ,0,O,"b",0,30,34,66,6(C),SB,0,0/"C
 "   , 0  , 0   , (C)  , 0   , O  , 30 . 62  , 0   , " d      , 124., S6 , 0
 ,0yO,0.0,0, "e"  , 0, 0,0,0,0,30, 34., 0
 ,"f",6S,56,0,0,0,0,0,0
2141 LET ns =o$( (SS-3) -1) +OS( (3?-3-
3))+o$(S?3);  LET n=d(S) .;  IF  n > ?
A THEN LET gO=5:  GO TO 2143
3142 LET go=0
3143 GO SUB 200
3145 NEXT  S           ....
3200 INPUT "TO play again  ?nput
 v'";y$:  IF yS'?"Y" THEN GO TO  21.^

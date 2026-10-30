   1 REM DIAMOND DIGGER
   2 REM Jim Provan 1983
   3 REM Typed by Paul Jenkinson
   5 BORDER 0: PAPER 0: INK 7: CLS 
   7 GO SUB 9000
  10 RESTORE 20: FOR x=USR "a" TO USR "t"+7: READ y: POKE x,y: NEXT x
  20 DATA 0,0,0,31,31,24,24,24,24,24,24,31,31,0,0,0,0,0,0,248,248,24,24,24,24,24,24,248,248,0,0,0
  30 DATA 24,24,24,31,31,24,24,24,24,24,24,248,248,24,24,24,24,24,24,255,255,0,0,0,0,0,0,255,255,24,24,24,24,24,24,24,24,24,24,24,0,0,0,255,255,0,0,0
  40 DATA 24,24,24,255,255,24,24,24,0,24,56,112,248,220,14,7,3,1,0,0,0,0,0,0,128,200,252,126,126,254,126,62
  50 DATA 0,0,63,127,255,255,255,127,0,0,252,254,255,255,255,254,63,31,15,7,3,1,0,0,252,248,240,224,192,128,0,0
  60 DATA 0,63,121,249,255,112,60,0,0,252,158,159,255,14,60,0
 100 LET screen=1
 105 LET diff=0
 110 LET score=0
 120 LET lives=3
 130 LET d=0
 140 LET p=1
 150 LET tot=0
 160 LET yp=19: LET xp=1
 170 IF screen=5 THEN LET screen=1: LET diff=diff+0.5
 180 LET tune=1
 200 GO SUB 1000*screen
 205 PRINT #0;AT 1,0; INVERSE 1;"000000"
 220 IF INKEY$="5" AND x>1 AND ATTR (yp,xp-3)<>7 THEN PRINT AT yp,xp; PAPER p;"  ";AT yp+1,xp;"  ": LET xp=xp-3: GO TO 260
 230 IF INKEY$="8" AND xp<28 AND ATTR (yp,xp+3)<>7 THEN PRINT AT yp,xp; PAPER p;"  ";AT yp+1,xp;"  ": LET xp=xp+3: GO TO 260
 240 IF INKEY$="6" AND yp<19 AND ATTR (yp+3,xp)<>7 THEN PRINT AT yp,xp; PAPER p;"  ";AT yp+1,xp;"  ": LET yp=yp+3: GO TO 260
 250 IF INKEY$="7" AND yp>1 AND ATTR (yp-3,xp)<>7 THEN PRINT AT yp,xp; PAPER p;"  ";AT yp+1,xp;"  ": LET yp=yp-3
 260 IF ATTR (yp,xp)=6 THEN LET score=score+100: LET tot=tot+1: LET p={10}{00}INT (RND*5)+1: GO TO 300
 270 LET p=INT (RND*6)+1
 300 PRINT AT yp,xp;"{9B}";AT yp+1,xp;"{9C}{9D}"
 305 BEEP .1,a(tune): LET tune=tune+1: IF tune=37 THEN LET tune=1
 310 IF RND>.9 THEN GO SUB 500
 320 PRINT #0;AT 1,7-LEN (STR$ score); INVERSE 1;score
 330 PRINT #0;AT 1,29;"{9D}-";lives
 340 IF tot=d THEN GO TO 800
 350 GO TO 210
 500 LET pos=INT (RND*9)*3+1
 505 IF RND<diff THEN LET pos=xp
 510 FOR h=1 TO 19 STEP 3
 515 LET paper=(ATTR (h,pos))/8-1
 517 IF paper=-.125 THEN LET paper=7
 520 PRINT INK 9; PAPER paper;AT h,pos;"{A2}{A3}"
 530 FOR n=1 TO 13: NEXT n: BEEP .1,a(tune): LET tune=tune+1: IF tune=37 THEN LET tune=1
 540 IF h=yp AND pos=xp THEN GO TO 600
 550 IF paper=-.125 THEN PRINT AT h,pos; INK 7;"{8F}{8F}"
 553 IF paper=-.25 THEN PRINT AT h,pos; INK 6;"{9E}{9F}"
 555 IF paper>0 THEN PRINT AT h,pos; PAPER paper;"  "
 560 NEXT h
 570 RETURN 
 600 FOR x=10 TO 0 STEP -1: BEEP .1,x: BEEP .1,x-1: BEEP .1,x-2: NEXT x
 610 LET lives=lives-1: IF lives=0 THEN GO TO 700
 620 GO TO 130
 700 RESTORE 710: FOR x=1 TO 7: READ a,b: BEEP a,b: NEXT x
 710 DATA 1,9,1,5,.5,4,.5,2,.5,1,.5,4,2,2
 720 IF INKEY$="" THEN GO TO 720
 730 RUN 
 800 FOR n=1 TO 2: RESTORE 805: FOR x=1 TO 7: READ a,b: BEEP a,b: NEXT x: NEXT n
 805 DATA .2,10,.4,10,.2,12,.4,12,.2,10,.4,8,.6,7
 810 CLS : PRINT : PRINT : FOR x=1 TO 18: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}": NEXT x
 815 PRINT #0;AT 1,0; INVERSE 1;"000000": PRINT #0;AT 1,7-LEN (STR$ score); INVERSE 1;score
 817 PRINT #0;AT 1,29;"{9D}-";lives
 820 LET p=INT (RND*9)*3+1
 825 LET i=0
 830 FOR n=1 TO 28 STEP 3
 835 LET i=i+1: IF i>7 THEN LET i=1
 840 PRINT AT 20,p; INK i;"{9E}{9F}";AT 21,p; INK i;"{A0}{A1}"
 850 PRINT AT 0,n;"{9B} ";AT 1,n;"{9C}{9D}": BEEP .1,n: PRINT AT 0,n;" ";AT 1,n;"  "
 870 IF INKEY$<>"" THEN GO TO 900
 880 NEXT n
 890 PRINT AT 0,28;" ";AT 1,30;" ": GO TO 830
 900 FOR x=1 TO 20: PRINT AT x-1,n;"  ";AT x,n;"{9B} ";AT x+1,n;"{9C}{9D}": BEEP .1,x+10: NEXT x
 910 IF n<>p THEN GO TO 600
 920 LET score=score+1000*i
 930 PRINT AT 0,11; INVERSE 1;"BONUS "; INVERSE 1;1000*i
 940 FOR x=1 TO 400: NEXT x
 950 LET screen=screen+1: GO TO 130
1000 CLS : PRINT "{90}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{92}"
1010 FOR x=1 TO 7: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}": NEXT x
1020 PRINT AT 21,0;"{91}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{93}"
1030 FOR x=1 TO 19 STEP 3: FOR y=1 TO 28 STEP 3: IF RND>.8 AND x<>18 AND y<>1 THEN PRINT AT x,y; INK 6;"{9E}{9F}";AT x+1,y; INK 6;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 1050
1040 LET i=INT (RND*5)+1: PRINT AT x,y; PAPER i;"  ";AT x+1,y; PAPER i;"  ": NEXT y: NEXT x
1050 RETURN 
2000 CLS : PRINT "{90}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{92}"
2010 FOR x=1 TO 2: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}": NEXT x
2020 PRINT AT 6,6;"{9A}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{9A}"
2030 FOR x=1 TO 3: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}                 {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{95}                 {94}{99}{99}{9A}{99}{99}{95}": NEXT x
2040 PRINT AT 15,6;"{9A}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{9A}"
2050 FOR x=1 TO 2: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}": NEXT x
2060 PRINT AT 21,0;"{91}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{93}"
2065 FOR x=7 TO 14: PRINT AT x,7;"{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}": NEXT x
2070 FOR x=1 TO 4 STEP 3: FOR y=1 TO 19 STEP 3: IF RND>.8 AND x<>1 AND y<>19 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x; INK 6;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 2090
2080 PRINT AT y,x; PAPER (INT (RND*6)+1);"  ";AT y+1,x;"  ": NEXT y: NEXT x
2090 FOR x=7 TO 22 STEP 3: FOR y=1 TO 4 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x; INK 6;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 2110
2100 PRINT AT y,x; PAPER (INT (RND*6)+1);"  ";AT y+1,x;"  ": NEXT y: NEXT x
2110 FOR x=7 TO 22 STEP 3: FOR y=16 TO 19 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x; INK 6;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 2130
2120 PRINT AT y,x; PAPER (INT (RND*6)+1);"  ";AT y+1,x;"  ": NEXT y: NEXT x
2130 FOR x=25 TO 28 STEP 3: FOR y=1 TO 19 STEP 3: IF RND>.8 AND y<>1 AND x<>19 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x; INK 6;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 2150
2140 PRINT AT y,x; PAPER (INT (RND*6)+1);"  ";AT y+1,x;"  ": NEXT y: NEXT x
2150 RETURN 
3000 CLS : PRINT "{90}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{99}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{92}"
3010 PRINT "{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{97}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}"
3020 PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{96}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {91}{99}{99}{9A}{99}{99}{9A}{99}{99}{96}{99}{99}{93}{8F}{8F}{8F}{8F}{8F}{91}{99}{99}{96}{99}{99}{9A}{99}{99}{9A}{99}{99}{93}  {8F}{8F}{98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}{8F}{8F}   {8F}{8F}{98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}{8F}{8F}  {90}{99}{99}{9A}{99}{99}{9A}{99}{99}{97}{99}{99}{92}{8F}{8F}{8F}{8F}{8F}{90}{99}{99}{97}{99}{99}{9A}{99}{99}{9A}{99}{99}{92}"
3030 PRINT "{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{97}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{96}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98} {91}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{93}     {91}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{93}"
3040 FOR x=1 TO 10 STEP 3: FOR y=1 TO 7 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 3070
3050 LET p=INT (RND*6)+1: PRINT AT y,x; PAPER p;"  ";AT y+1,x;"  ": NEXT y: NEXT x: GO TO 3070
3070 FOR x=1 TO 10 STEP 3: FOR y=13 TO 19 STEP 3: IF RND>.8 AND y<>19 AND x<>1 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 3090
3080 LET p=INT (RND*6)+1: PRINT AT y,x; PAPER p;"  ";AT y+1,x;"  ": NEXT y: NEXT x: GO TO 3090
3090 FOR x=19 TO 28 STEP 3: FOR y=13 TO 19 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 3110
3100 LET p=INT (RND*6)+1: PRINT AT y,x; PAPER p;"  ";AT y+1,x;"  ": NEXT y: NEXT x: GO TO 3110
3110 FOR x=19 TO 28 STEP 3: FOR y=1 TO 7 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 3130
3120 LET p=INT (RND*6)+1: PRINT AT y,x; PAPER p;"  ";AT y+1,x;"  ": NEXT y: NEXT x: GO TO 3130
3130 BEEP .5,-4: PRINT AT 10,4; PAPER INT (RND*6)+1;"  ";AT 11,4;"  ";AT 4,13;"  ";AT 5,13;"  "; PAPER INT (RND*6)+1;AT 4,16; PAPER INT (RND*6)+1;"  ";AT 5,16;"  "
3140 PRINT AT 16,13; PAPER INT (RND*6)+1;"  ";AT 17,13;"  ";AT 16,16; PAPER INT (RND*6)+1;"  ";AT 17,16;"  ";AT 10,25; PAPER INT (RND*6)+1;"  ";AT 11,25;"  "
3150 RETURN 
4000 CLS : PRINT "         {90}{99}{99}{97}{99}{99}{97}{99}{99}{97}{99}{99}{92}         "
4010 FOR x=1 TO 4 STEP 3: PRINT " {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}   {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}   {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}": NEXT x
4020 PRINT AT 6,0;"{90}{99}{99}{97}{99}{99}{97}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{92}"
4030 FOR x=7 TO 13 STEP 3: PRINT "{98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98}  {98} {94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}": NEXT x
4040 PRINT AT 15,0;"{91}{99}{99}{96}{99}{99}{96}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{96}{99}{99}{96}{99}{99}{93}"
4050 FOR x=1 TO 4 STEP 3: PRINT " {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}   {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{98}  {98}  {98}  {98}  {98}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}   {8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{94}{99}{99}{9A}{99}{99}{9A}{99}{99}{9A}{99}{99}{95}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}": NEXT x
4060 PRINT AT 21,0;"         {91}{99}{99}{96}{99}{99}{96}{99}{99}{96}{99}{99}{93}         "
4070 LET xp=10: LET yp=19
4090 FOR x=10 TO 19 STEP 3: FOR y=1 TO 19 STEP 3: IF RND>.8 AND x<>10 AND y<>19 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 4110
4100 PRINT AT y,x; PAPER INT (RND*6)+1;"  ";AT y+1,x;"  ": NEXT y: NEXT x
4110 FOR x=1 TO 7 STEP 3: FOR y=7 TO 13 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 4130
4120 PRINT AT y,x; PAPER INT (RND*6)+1;"  ";AT y+1,x;"  ": NEXT y: NEXT x
4130 FOR x=22 TO 29 STEP 3: FOR y=7 TO 13 STEP 3: IF RND>.8 THEN PRINT AT y,x; INK 6;"{9E}{9F}";AT y+1,x;"{A0}{A1}": LET d=d+1: NEXT y: NEXT x: GO TO 4150
4140 PRINT AT y,x; PAPER INT (RND*6)+1;"  ";AT y+1,x;"  ": NEXT y: NEXT x
4150 RETURN 
9000 DIM a(36): RESTORE 9010: FOR x=1 TO 36: READ a(x): BEEP .2,a(x): NEXT x
9010 DATA 0,0,4,4,5,5,7,7,0,0,4,4,2,2,-5,-5,0,0,4,4,5,5,7,7,2,4,2,4,2,-5,2,-5,2,4,2,4,2,2
9020 RETURN 

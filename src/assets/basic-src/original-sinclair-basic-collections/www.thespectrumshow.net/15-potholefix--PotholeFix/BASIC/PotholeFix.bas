   1 RESTORE 
   2 BORDER 4
   3 CLS 
  10 FOR n=0 TO 7
  20 READ a: POKE USR "a"+n,a
  30 NEXT n
  40 FOR n=0 TO 7
  50 READ b: POKE USR "b"+n,b
  60 NEXT n
  65 INPUT "Instructions? (y or n)";a$
  66 IF a$="y" THEN GO TO 2000
  70 LET k=10: LET p=11: LET op=p: LET sc=0
  75 POKE 23692,255
  80 PRINT AT 21,0; INK 3;"{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}";AT 21,k; BRIGHT 1;"     ": IF RND>.8 THEN PRINT AT 21,k+(INT (RND*4)+1); BRIGHT 1; INK 0;"{91}"
  81 PRINT '
  82 PRINT AT 0,0;"Score= ";sc
  83 LET sc=sc+1
  84 PRINT AT 10,p; BRIGHT 1; INK 1;"{90}";AT 9,op;" ": REM SCREEN$ (9,p)
  86 IF INKEY$<>"5" AND INKEY$<>"8" AND ATTR (11,p)<>56 AND ATTR (11,p)<>123 THEN GO TO 1000
  87 IF INKEY$="5" AND ATTR (11,p-1)<>56 AND ATTR (11,p-1)<>123 THEN GO TO 1000
  88 IF INKEY$="8" AND ATTR (11,p+1)<>56 AND ATTR (11,p+1)<>123 THEN GO TO 1000
  90 LET op=p
 100 LET p=p+(INKEY$="8")-(INKEY$="5")
 110 LET o=INT (RND*3)+1
 120 IF o=1 THEN LET k=k-1
 130 IF o=3 THEN LET k=k+1
 140 IF k<2 THEN LET k=2
 150 IF k>26 THEN LET k=26
 160 GO TO 75
1000 REM Hit Something
1010 FOR f=1 TO 100
1020 OUT 254,RND*255
1030 NEXT f
1040 FOR f=50 TO -50 STEP -2
1050 BEEP .005,f
1060 NEXT f
1070 CLS 
1080 FOR f=0 TO 21 STEP 2
1090 PRINT AT f,0;" {11}{00}{10}{07}       YOURE DEAD HA HA       {11}{07}{10}{00} ";AT f+1,0; INK 1;"{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}": NEXT f
1100 INPUT "Score=";(sc);", Another go (y or n)";a$
1110 IF a$="y" THEN CLS : GO TO 1
1120 STOP 
2000 REM instructions
2010 CLS 
2020 PRINT AT 0,11;"Pothole";AT 0,11; OVER 1;"_______"
2030 PRINT AT 3,1;"You are a potholer and you must";AT 5,1;"try to manoeuvre youre man down";AT 7,1;"inside a deep cave using keys";AT 9,1;"5 for left and 8 for right";AT 11,11;"Good Luck!"
2040 FOR f=1 TO 100
2050 BEEP .05,RND: NEXT f
2060 PAUSE 0: CLS : GO TO 70
9000 DATA 24,90,60,28,24,36,66,0,64,188,132,130,65,130,122,4
9900 SAVE "Pothole" LINE 1

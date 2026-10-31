   1 REM Carols
   2 RESTORE 50
   3 REM Typed by Paul Jenkinson
   4 BORDER 0: PAPER 0: INK 6: CLS 
   5 CLS : PRINT AT 10,(31-22)/2;"PRESS ANY KEY TO BEGIN.": PAUSE 0: CLS 
   8 PRINT '"Good king wenceslas"
   9 FOR d=1 TO 2
  10 LET a=.4
  20 READ b,c: IF b=99 THEN RESTORE 50: PAUSE 50: NEXT d: GO TO 56
  30 BEEP b,c
  40 GO TO 20
  50 DATA a,9,a,9,a,9,a,11,a,9,a,9,2*a,4,a,6,a,4,a,6,a,8,2*a,9,2*a,9
  51 DATA a,9,a,9,a,9,a,11,a,9,a,9,2*a,4,a,6,a,4,a,6,a,8,2*a,9,2*a,9
  52 DATA a,16,a,14,a,13,a,11,a,13,a,11,2*a,9
  53 DATA a,6,a,4,a,6,a,8,2*a,9,2*a,9
  54 DATA a,4,a,4,a,6,a,8,a,9,a,9,2*a,11
  55 DATA a,16,a,14,a,13,a,11,2*a,9,2*a,14,4*a,9,99,99
  56 PAUSE 50: PRINT '"O come all ye faithful"
  57 RESTORE 65: FOR d=1 TO 2
  58 LET a=.4
  59 READ b,c: IF b=99 THEN RESTORE 65: PAUSE 50: NEXT d: GO TO 90
  60 BEEP b,c
  61 GO TO 59
  65 DATA a,4,a*2,4,a,-1,a,4,2*a,6,2*a,-1,a,8,a,6,a,8,a,9,2*a,8,a,6
  66 DATA a,4,2*a,4,a,3,a,1,a,3,a,4,a,6,a,8,2*a,3,a*1.5,1,.2,-1,a*3,-1
  67 DATA 2*a,11,a,9,a,8,2*a,9,2*a,8,a,6,a,8,a,4,a,6,1.4*a,3,a/2,1,a,-1
  68 DATA a,4,a,4,a,3,a,4,a,6,2*a,4,1*a,-1
  69 DATA a,8,a,8,a,6,a,8,a,9,2*a,8,a,6
  70 DATA a,8,a,9,a,8,a,6,a,4,2*a,3,a,4,a,9,2*a,8,2*a,6,a/2,4,2,4
  71 DATA 99,99
  90 PAUSE 50: PRINT '"The first nowell"
  91 RESTORE 10: FOR d=1 TO 2
  92 LET a=.4
  93 READ b,c: IF b=99 THEN RESTORE 100: PAUSE 50: NEXT d: GO TO 115
  94 BEEP b,c
  95 GO TO 93
 100 DATA a/2,6,a/2,4,a*1.5,2,a/2,4,a/2,6,a/2,7,2*a,9,a/2,11,a/2,13,a,14,a,13,a,11,2*a,9
 101 DATA a/2,11,a/2,13,a,14,a,13,a,11,a,9,a,11,a,13,a,14,a,9,a,7,2*a,6
 102 DATA a/2,6,a/2,4,a*1.5,2,a/2,4,a/2,6,a/2,7,2*a,9,a/2,11,a/2,13,a,14,a,13,a,11,2*a,9
 103 DATA a/2,11,a/2,13,a,14,a,13,a,11,a,9,a,11,a,13,a,14,a,9,a,7,2*a,6
 104 DATA a/2,6,a/2,4,a*1.5,2,a/2,4,a/2,6,a/2,7,2*a,9,a/2,14,a/2,13,2*a,11,a,11,1.5*a,9,a,14,a,13,a,11,a,9,a,11,a,13,a,14,a,9,a,7,2,6
 105 DATA 99,99
 115 PRINT '"While shepherds watch thier     flocks by night.": RESTORE 120: FOR n=1 TO 2
 116 READ b,c: IF b=99 THEN RESTORE 120: PAUSE 20: NEXT n: PAUSE 50: GO TO 200
 117 BEEP b*1.5,c: GO TO 116
 120 DATA a,5,a*1.5,9,a/1.5,9,a,7,a,5,a,10,a,10,a,9,a,7,a,9,a,12,a,12,a,11,a*2,12
 130 DATA a,9,a*1.5,14,a/1.5,12,a,10,a,9,a,7,a,5,a,4,a,9,a,7,a,5,a,5,a,4,a*2,5
 140 DATA 99,99
 200 RESTORE 220
 205 PRINT '"Hark the herold angels sing."
 206 RESTORE 220: FOR n=1 TO 2
 210 READ b,c: IF b=99 THEN RESTORE 220: PAUSE 20: NEXT n: PAUSE 50: GO TO 300
 215 BEEP b,c: GO TO 210
 220 DATA a,2,a,7,a*1.5,7,a/1.5,6,a,7,a,11,a,11,a,9,a,14,a,14,a*1.5,14,a/1.5,12,a,11,a,9,a*2,11
 225 DATA a,2,a,7,a*1.5,7,a/1.5,6,a,7,a,11,a,9,a,14,a,9,a*1.5,9,a/1.5,6,a,6,a,4,a*2,2
 230 DATA a,14,a,14,a,14,a,7,a,12,a,11,a,11,a,9
 235 DATA a,14,a,14,a,14,a,7,a,12,a,11,a,11,a,9
 240 DATA a*1.5,16,a/1.5,16,a,16,a,14,a,12,a,11,a*1.5,12,a,9,a/1.5,11,a/1.5,12,a*1.5,14,a/1.5,7,a,7,a,9,a*2,11
 250 DATA a*1.5,16,a/1.5,16,a,16,a,14,a,12,a,11,a*1.5,12,a,9,a/1.5,11,a/1.5,12,a*1.5,14,a/1.5,7,a,7,a,9,a*2,7
 260 DATA 99,99
 300 LET s=2: PRINT '"It came upon the midnight clear."
 310 FOR n=0 TO 1: RESTORE 330
 315 READ b,c: IF b=99 THEN PAUSE 20: NEXT n: PAUSE 50: GO TO 400
 320 BEEP b*1.5,c: GO TO 315
 330 DATA a/s,5,a/s,7,a,9,a,7,a,5,a/s,7,a/s,9,a,10,a,9,a,7,a,12,a,12,a,9,a/s,10,a/s,12,a,14,a*s,12
 340 DATA a/s,9,a/s,10,a,12,a,12,a,9,a,5,a,10,a,9,a,7,a/s,5,a/s,7,a/s,9,a/s,10,a,12,a,9,a,7,a*s,5
 350 DATA a,5,a,4,a,2,a,4,a,7,a*s,5,a/s,4,a,2,a,9,a,7,a,5,a,4,a,2,a*s,0
 360 DATA a,0,a,12,a,10,a,9,a/s,7,a/s,9,a,10,a,9,a,7,a/s,5,a/s,7,a/s,9,a/s,10,a,12,a,9,a,7,a*2,5
 370 DATA 99,99
 400 PRINT '"O little town of Bethlahem."
 410 FOR n=0 TO 1: RESTORE 430
 420 READ b,c: IF b=99 THEN PAUSE 20: NEXT n: PAUSE 50: GO TO 5
 425 BEEP b,c: GO TO 420
 430 DATA a*s,2,a*s,7,a*s,7,a*s,7,a*s,9,a,11,a,9,a,11,a,12,a*s,14,a*s,11,a*s,12,a,11,a,7,a*s,9,a*s,9,a*(s*1.5),7
 440 DATA a*s,2,a*s,7,a*s,7,a*s,7,a*s,9,a,11,a,9,a,11,a,12,a*s,14,a*s,11,a*s,12,a,11,a,7,a*s,9,a*s,9,a*(s*1.5),7
 450 DATA a,7,a,11,a*(s*1.5),14,a,16,a,14,a,12,a,11,a,9,a,7,a,9,a,11,a,12,a*s,14,a*s,2,a*s,7,a*s,11,s*a,9,a*s,7,a*(s*1.5),2
 460 DATA a*s,2,a*s,7,a*s,7,a*s,7,a*s,9,a,11,a,9,a,11,a,12,a*s,14,a*s,11,a*s,12,a,11,a,7,a*s,9,a*s,9,a*(s*1.5),7
 600 DATA 99,99
9997 RESTORE 450: GO TO 420
9998 SAVE "C CAROLS" LINE 1
9999 POKE 23693,56: BORDER 7

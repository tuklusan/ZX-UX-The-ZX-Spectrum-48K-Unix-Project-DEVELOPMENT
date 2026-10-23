5 LET hs=0
10 PAPER 0: CLS : BORDER 0
20 FLASH 0: OVER 0: INVERSE 0
30 BRIGHT 0
35 PRINT AT 10,0; FLASH 1; INK 4;"STOP THE TAPE - PRESS ANY KEY"
40 PAUSE 0: CLS: PRINT INK 2;"RED"; INK 7;" CARPET": PRINT "For the 16K ZX Spectrum": PRINT "By Gavin Devine": PRINT "Move Chris the carpet layer about the maze laying the Queens Red Carpet as she is about to take her first steps into the stars. One problem: The carpet and stars have burglar alarms and if Chris touches them he will be destroyed. Use: Z-Left, X-Right, C-Down, F-Up. Press S to start."
45 PAUSE 600
46 IF INKEY$<>"s" THEN GO TO 45
50 RESTORE
70 FOR f=USR "a" TO USR "b"+7
80 READ a: POKE f,a
90 NEXT f
100 LET s=0
120 PRINT AT 2,0; INK 5;" ******************************"
121 PRINT AT 3,0; INK 5;"**              *"
122 PRINT AT 4,0; INK 5;"** ** ********* * ********** **"
123 PRINT AT 5,0; INK 5;"** **         * * *          **"
124 PRINT AT 6,0; INK 5;"** ********** * * * ***********"
125 PRINT AT 7,0; INK 5;"**"
126 PRINT AT 8,0; INK 5;"** ****************************"
127 PRINT AT 9,0; INK 5;"**"
128 PRINT AT 10,0; INK 5;"******* ********** ******* ****"
129 PRINT AT 11,0; INK 5;"**    *                    *"
130 PRINT AT 12,0; INK 5;"** **   *******   ********   **"
131 PRINT AT 13,0; INK 5;"** **         *   *          **"
132 PRINT AT 14,0; INK 5;"**    * ***** * * * ****** *"
133 PRINT AT 15,0; INK 5;"*******         *          ****"
134 PRINT AT 16,0; INK 5;" **      ******************"
135 PRINT AT 17,0; INK 5;" ** **** *                    **"
136 PRINT AT 18,0; INK 5;" **"
137 PRINT AT 19,0; INK 6;"        ***********"
138 PRINT AT 20,0; INK 6;"                 ******  *******"
139 PRINT AT 21,0; INK 6;"******************"
140 LET a=18: LET b=10
145 LET e=-1: LET f=0
150 PRINT AT a,b; INK 7;CHR$(144)
160 BEEP .01,0: BEEP .01,1: BEEP .01,2: BEEP .01,3: BEEP .01,4: BEEP .01,5: BEEP .01,6: BEEP .01,7
170 IF INKEY$="z" THEN LET e=-1 : LET f=0
180 IF INKEY$="x" THEN LET e=1: LET f=0
190 IF INKEY$="c" THEN LET f=1: LET e=0
200 IF INKEY$="f" THEN LET f=-1: LET e=0
210 PRINT AT a,b; INK 2;CHR$(143)
220 IF SCREEN$ (a+f,b+e)="*" THEN GO TO 250
225 IF ATTR (a+f,b+e)=BIN 00000010 THEN GO TO 250
230 LET s=s+1: LET a=a+f: LET b=b+e
235 PRINT AT 0,0; INK 7; INVERSE 1;"SCORE=";s;" HI=";hs
240 GO TO 160
250 PRINT AT a+f,b+e; FLASH 1; INK 6; PAPER 2;CHR$(145): FOR f=1 TO 20: BEEP .01,5: NEXT f: BEEP .1,10: BEEP .01,10
260 IF s>hs THEN GO TO 300
270 PRINT AT 21,0;"Instructions (y/n) ?": INPUT a$: IF a$="y" THEN CLS : GO TO 40
280 CLS
290 GO TO 100
300 CLS : PAPER 6: CLS
310 INK 0
320 LET B$=CHR$(143): PRINT AT 1,3;B$+"   "+B$+" "+B$+B$+B$+B$+B$+"  "+B$+B$+B$+B$+" "+B$+"   "+B$: PRINT AT 2,3;B$+"   "+B$+"   "+B$+"   "+B$+"     "+B$+"   "+B$: PRINT AT 3,3;B$+B$+B$+B$+B$+"   "+B$+"   "+B$+" "+B$+B$+B$+" "+B$+B$+B$+B$+B$: PRINT AT 4,3;B$+"   "+B$+"   "+B$+"   "+B$+"   "+B$+" "+B$+"   "+B$: PRINT AT 5,3;B$+"   "+B$+" "+B$+B$+B$+B$+B$+"  "+B$+B$+B$+B$+" "+B$+"   "+B$
330 PRINT AT 10,1;" "+B$+B$+B$+B$+"  "+B$+B$+B$+B$+"  "+B$+B$+B$+"  "+B$+B$+B$+B$+"  "+B$+B$+B$+B$+B$: PRINT AT 11,1;B$+"     "+B$+"     "+B$+"   "+B$+" "+B$+"   "+B$+" "+B$+"    ": PRINT AT 12,1;" "+B$+B$+B$+"  "+B$+"     "+B$+"   "+B$+" "+B$+B$+B$+B$+"  "+B$+B$+B$+B$+" ": PRINT AT 13,1;"    "+B$+" "+B$+"     "+B$+"   "+B$+" "+B$+"  "+B$+"  "+B$+"    ": PRINT AT 14,1;B$+B$+B$+B$+"   "+B$+B$+B$+B$+"  "+B$+B$+B$+"  "+B$+"   "+B$+" "+B$+B$+B$+B$+B$
340 PRINT AT 17,1;CHR$(143);CHR$(143);" HI=";hs;"  "
350 PRINT AT 19,1;CHR$(143);CHR$(143);CHR$(143);"   ";CHR$(143);CHR$(143);CHR$(143)
360 FOR f=1 TO 250: NEXT f
370 PRINT AT 17,1;B$+"   "+B$+" "+B$+B$+B$+B$+B$+" "+B$+"   "+B$: PRINT AT 18,1;B$+B$+"  "+B$+" "+B$+"     "+B$+"   "+B$: PRINT AT 19,1;B$+" "+B$+" "+B$+" "+B$+B$+B$+B$+"  "+B$+" "+B$+" "+B$: PRINT AT 20,1;B$+"  "+B$+B$+" "+B$+"     "+B$+B$+" "+B$+B$: PRINT AT 21,1;B$+"   "+B$+" "+B$+B$+B$+B$+B$+" "+B$+"   "+B$
380 FOR f=1 TO 25: PRINT AT 21,f;s: BEEP .05,f: PRINT AT 21,f-1;" ": NEXT f
390 FOR f=21 TO 10 STEP -1: PRINT AT f,25;s: BEEP .05,f: PRINT AT f,25;" ": NEXT f
400 FOR f=25 TO 14 STEP -1: PRINT AT 18,f+3;" "; AT 18,f;s: BEEP .05,f: NEXT f
410 PRINT AT 18,14;s;" "
412 FLASH 0: PAPER 0: INK 7
420 LET hs=s: GO TO 270
1000 DATA 24,24,126,24,24,36,36,36
1010 DATA 153,90,60,255,255,60,90,153

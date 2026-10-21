1 RANDOMIZE :BORDER 7:PAPER 7:INK 0:CLS :GO SUB 7000:CLS
2 INPUT "How many races would you like   there to be at this meeting ?  ";races
3 INPUT "How many punters are there?",a
4 DIM p(a):FOR c=1TO a
5 LET p(c)=200
6 NEXT c
10 GO SUB 9000
20 CLS :GO SUB 1999
100 FOR c=2TO 12STEP 2
105 PRINT INK c/2;AT c,0;c/2;" {90}"
106 PRINT AT c-1,2;"{8F}"
107 NEXT c
108 PLOT 251,170:DRAW 0,-102
109 PRINT AT 13,2;"{8F}":PRINT AT 0,31;OVER 1;"o"
110 LET a$="FINISH":FOR c=1TO 6:PRINT AT 13+c,31;a$(c):NEXT c
115 FOR c=163TO 67STEP -16:PLOT 24,c:DRAW 227,0:NEXT c
120 GO SUB 1000
1000 BEEP .5,0:PRINT AT 14,0;"READY":BEEP .5,6:PRINT AT 14,0;"STEADY":BEEP .5,12:PRINT AT 14,0;"GO    ":BEEP .5,18:PRINT AT 14,0;"  "
1001 LET ge=0:DIM x(6):FOR c=1TO 6:LET x(c)=2:NEXT c
1002 FOR c=1TO 6
1004 BEEP .03,-20:BEEP .03,-30
1005 LET x(c)=x(c)+(f(c)=1AND RND <.8)+(f(c)=2AND RND <.77)+(f(c)=4AND RND <.74)+(f(c)=8AND RND <.71)+(f(c)=16AND RND <.68)+(f(c)=32AND RND <.65)
1006 PRINT INK c;AT c*2,x(c)-1;" {90}"
1008 IF x(c)=31THEN LET ge=1
1009 BEEP .03,-20:BEEP .03,-30
1015 NEXT c
1020 IF ge=1THEN GO TO 1050
1040 GO TO 1002
1050 DIM h(6):LET many=0:FOR c=1TO 6
1052 IF x(c)=31THEN LET many=many+1:LET h(many)=c
1053 NEXT c
1054 IF many=1THEN LET winner=h(1):GO TO 1090
1055 PRINT AT 20,0;"There is a photo-finish between these horses:  "
1056 PRINT AT 21,15;h(1);"  ";h(2);"  ";
1057 IF many=3THEN PRINT ;h(3);
1058 IF many=4THEN PRINT ;"  ";h(4)
1060 FOR c=1TO 300
1065 NEXT c
1067 LET er=INT (RND *4)+1
1070 LET winner=h(er)
1071 IF winner=0THEN GO TO 1067
1075 IF RND <.33THEN LET g$="a short head":GO TO 1079
1076 IF RND <.4THEN LET g$="a neck":GO TO 1079
1077 LET g$="1 length"
1079 PRINT AT 20,0;"                                                   "
1080 PRINT AT 20,1;"The winner is ";winner;" who won by":PRINT AT 21,1;g$
1081 PAUSE 130
1082 CLS
1085 GO TO 1100
1090 PRINT AT 20,1;"The winner is ";winner;" who won by ":PRINT " ";INT (RND *3)+2;" lengths."
1095 PAUSE 130:CLS
1100 FOR r=1TO a
1101 IF p(r)=0THEN LET r=r+1:GO TO {12}{00}(1101AND r<a+1)+(1130AND r=a+1)
1105 IF e(r)=winnerTHEN LET p(r)=p(r)+b(r)*f(winner):GO TO 1115
1110 LET p(r)=p(r)-b(r)
1115 IF p(r)<= 0THEN GO TO 8000
1117 IF e(r)<> winnerTHEN GO TO 1125
1120 CLS :PRINT AT 10,4;"Well done punter ";r;" !"'"Your horse won and you now have £";p(r):PAUSE 0:GO TO 1130
1125 CLS :PRINT AT 10,4;"Bad luck punter ";r;" !"'"Your horse did not win, and so  you now have £";p(r):PAUSE 0
1130 NEXT r
1150 GO TO 20
1999 LET races=races-1:IF races=-1THEN GO TO 6000
2000 DIM f(6):FOR c=1TO 6:LET f(c)=2↑(INT (RND *6)):NEXT c
2020 PRINT "The tipsters reckon the betting:"
2025 FOR c=1TO 6:PRINT INK c;PAPER (7AND c<4)+(0AND c>3);AT 2*c,2;"HORSE ";c;"    ";f(c);":1"
2026 IF f(c)=1THEN PRINT INK c;PAPER (0AND c>3)+(7AND c<4);AT 2*c,13;"EVENS"
2029 NEXT c
2030 DIM e(a):DIM b(a):FOR f=1TO a
2031 IF p(f)=0THEN LET f=f+1:GO TO (2031AND f<a+1)+(2050AND f=a+1)
2032 PRINT AT 14,1;"Punter ";f;" :":PRINT '"You have £";p(f);".       ":PRINT "How much would you like to bet?"
2033 INPUT b(f):IF b(f)>p(f)THEN GO TO 2033
2034 IF b(f)<> INT (b(f))THEN GO TO 2033
2035 PRINT '"On which horse is this to be    placed?"
2036 INPUT e(f)
2037 IF e(f)<1OR e(f)>6THEN GO TO 2036
2038 PRINT AT 17,0;"                                       "
2039 PRINT AT 19,0;"                                           "
2040 NEXT f
2050 CLS :RETURN
6000 PRINT "THE MEETING IS NOW FINISHED"
6010 FOR f=1TO a
6016 IF p(f)=0THEN LET f=f+1:GO TO (6015AND f<a+1)+(6040AND f=a+1)
6020 PRINT '"Punter ";f;" finishes with £";p(f)
6030 NEXT f
6040 PRINT INVERSE 1;'"Press and key to play again.":PAUSE 0:RUN
7000 PRINT ''"     {8F} {8F} {8F}{8F}{8F} {8F}{8F}{8F} {8F}{8F}{8F} {8F}{8F}{8F}             {8F} {8F} {8F} {8F} {8F} {8F} {8F}   {8F}               {8F}{8F}{8F} {8F} {8F} {8F}{8F}{8F} {8F}{8F}{8F} {8F}{8F}              {8F} {8F} {8F} {8F} {8F}{8F}    {8F} {8F}               {8F} {8F} {8F}{8F}{8F} {8F} {8F} {8F}{8F}{8F} {8F}{8F}{8F}"
7010 PRINT ''"       {8F}{8F}{8F}  {8F}  {8F}{8F}{8F} {8F}{8F}{8F}                 {8F} {8F} {8F} {8F} {8F}   {8F}                   {8F}{8F}{8F} {8F}{8F}{8F} {8F}   {8F}{8F}                  {8F}{8F}  {8F} {8F} {8F}   {8F}                   {8F} {8F} {8F} {8F} {8F}{8F}{8F} {8F}{8F}{8F}"
7020 PRINT ''"A gambling game for the whole              famiy"''"       @  Paul Stanley":PAUSE 300:RETURN
8000 CLS :PRINT AT 5,0;"Tut Tut! Punter ";r;", you have":PRINT "run out of money."
8005 PRINT :PRINT "I must therefore not let you betany more."
8010 PRINT '"However, if your rules are to   allow cheating, if you press ";INVERSE 1;"C";:PRINT ;"  I will give you £50 more."
8020 PRINT "Otherwise press ";INVERSE 1;"X";INVERSE 0;" and I will    cancel you from the game"
8030 IF INKEY$ ="x"OR INKEY$ ="X"THEN LET p(r)=0:GO TO 8050
8040 IF INKEY$ ="c"OR INKEY$ ="C"THEN LET p(r)=50:GO TO 8050
8045 GO TO 8030
8050 CLS :GO TO 1130
9000 FOR c=USR "a"TO USR "a"+7:READ v:POKE c,v:NEXT c
9001 DATA 16,BIN 00011011,18,254,61,BIN 01100110,BIN 10101010,34
9999 RETURN

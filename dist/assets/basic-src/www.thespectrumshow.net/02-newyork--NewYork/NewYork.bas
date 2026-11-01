   4 LET j=0
   5 LET sc=0
   6 LET bh=0
   8 LET aw=1
   9 BORDER 0: PAPER 0: INK 7: CLS 
  10 LET k=0
  12 LET c=0
  15 LET i=0
  20 POKE USR "a",BIN 0
  21 POKE USR "a"+1,BIN 01000001
  22 POKE USR "a"+2,BIN 00100010
  23 POKE USR "a"+3,BIN 00011100
  24 POKE USR "a"+4,BIN 00101010
  25 POKE USR "a"+5,BIN 01011101
  26 POKE USR "a"+6,BIN 01001001
  27 POKE USR "a"+7,BIN 01000001
  30 POKE USR "b",BIN 10001000
  31 POKE USR "b"+1,BIN 01101001
  32 POKE USR "b"+2,BIN 10111010
  33 POKE USR "b"+3,BIN 00011100
  34 POKE USR "b"+4,BIN 11111111
  35 POKE USR "b"+5,BIN 11011101
  36 POKE USR "b"+6,BIN 10101110
  37 POKE USR "b"+7,BIN 01101011
  40 FOR g=1 TO 2: READ p$: FOR f=0 TO 7: READ s: POKE USR p$+f,s: NEXT f: NEXT g
  41 DATA "c",60,126,153,153,255,153,153,255
  42 DATA "d",255,153,153,255,255,153,153,255
  50 POKE USR "n",BIN 00000001
  51 POKE USR "n"+1,BIN 00000111
  52 POKE USR "n"+2,BIN 00011010
  53 POKE USR "n"+3,BIN 11101010
  54 POKE USR "n"+4,BIN 01111111
  55 POKE USR "n"+5,BIN 00011111
  56 POKE USR "n"+6,BIN 00000011
  57 POKE USR "n"+7,BIN 00000001
  58 POKE USR "m",BIN 10000000
  59 POKE USR "m"+1,BIN 11100000
  60 POKE USR "m"+2,BIN 01011000
  61 POKE USR "m"+3,BIN 01010111
  62 POKE USR "m"+4,BIN 11111110
  63 POKE USR "m"+5,BIN 11111000
  64 POKE USR "m"+6,BIN 11000000
  65 POKE USR "m"+7,BIN 10000000
  75 GO SUB 2000
  85 BORDER 0: PAPER 0: INK 7: CLS 
  89 LET z=0: FOR m=0 TO 50: INK INT (RND*6)+1: PLOT BRIGHT 1;INT (RND*255),175-INT (RND*125): NEXT m
  90 INK 7
  91 LET z=z+INT (RND*1)+1
  92 FOR u=21 TO (21-INT (RND*le)) STEP -1: PRINT AT u,z; INK 4; BRIGHT 1;"{93}": PRINT AT u-1,z; INK 4; BRIGHT 1;"{92}": NEXT u
  93 IF z<=29 THEN GO TO 91
  94 PRINT AT 21,1; INK 4;"{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}{8F}"
  95 IF aw>=0 THEN LET bh=bh+1: LET x=19-bh: LET y=13
  97 PRINT AT 21,8; INK 1; PAPER 4;"New-York by night{11}{02}{11}{00}"{11}{00}
  98 PRINT AT 5,9;"Attack wave ";aw: LET c=0
  99 PAUSE 100: PRINT AT 5,9;"               "
 100 PRINT AT 0,0; FLASH 1;"Score = ";sc: PRINT FLASH 1;"Level ";le: LET c=c+1
 101 LET k=0
 102 LET l=INT (RND*29)+1
 103 FOR f=0 TO 21
 104 PRINT AT x,y; INK 2; BRIGHT 1;"__"
 110 IF INKEY$="q" AND y>1 THEN LET y=y-2: PRINT AT x,y+2;"  "
 120 IF INKEY$="e" AND y<28 THEN LET y=y+2: PRINT AT x,y-2;"  "
 210 PRINT AT k,l; BRIGHT 1;"{90}"
 215 PRINT AT k-1,l;" "
 220 LET k=k+1
 225 IF k=22 AND c>=20 THEN LET aw=aw+1: GO TO 5004
 230 IF ATTR (x,y)=71 OR ATTR (x,y+1)=71 THEN GO TO 1000
 232 IF ATTR (k,l)=4 OR (ATTR (k,l)>=32 AND ATTR (k,l)<=39) THEN LET i=i+1: BEEP .03,30: BEEP .09,45: BEEP .06,20
 235 IF i=27 THEN GO TO 5000
 240 NEXT f
 500 GO TO 100
1000 BEEP .07,10: PRINT AT x,y;"{91}{91}"
1005 LET sc=sc+1
1010 GO TO 100
2000 PRINT "New York by night is a typical ": PRINT 
2005 PRINT "invader game. The aim is to ": PRINT 
2010 PRINT "destroy the aliens which are ": PRINT 
2015 PRINT "attempting to flatten New York.": PRINT 
2020 PRINT "You are in control of a flying ": PRINT 
2025 PRINT "disc which has an antimatter ": PRINT 
2030 PRINT "surface. The aliens, on contact ": PRINT 
2035 PRINT "with your disc, self-destruct. ": PRINT 
2040 PRINT "You flight controls are:": PRINT 
2060 PRINT "Q.....Left, E.....Right": PRINT 
2072 PRINT : PRINT "Hit any key"
2075 PRINT AT 21,13; INK 3; FLASH 1;"Author: P Watson"
2080 PAUSE 0: CLS 
2100 INPUT "Level of difficulty(1-8)";le: LET bh=le
2110 IF le<1 OR le>8 THEN GO TO 2100
2300 RETURN 
5000 PRINT AT k,l; BRIGHT 1;"{90}": PRINT AT k-1,l;" ": PRINT AT 5,0; INK 2; BRIGHT 1; FLASH 1;"A sufficient amount of New-York has been destroyed. The aliens             are leaving          "
5001 PRINT AT 5,31;" ": PRINT AT 6,31;" ": PRINT AT 7,31;" "
5004 IF i<>27 THEN PRINT AT 5,0; FLASH 1; INK 3;"  Attack Wave ";aw-1;" is complete,a     mother ship will pick up the    aliens - Prepare for the next   attack wave                   "
5005 FOR v=0 TO 350: NEXT v
5006 PRINT AT 5,0;"                                                                                                                                "
5008 LET d=31
5010 FOR w=1 TO 29: LET q=2: FOR r=21 TO 2 STEP -1
5015 PRINT AT q,w-1;"{9D}{9C}"
5016 IF w>=2 THEN PRINT AT q,w-2;"   "
5018 IF ATTR (21,w)<>71 AND ATTR (21,w)<>7 AND ATTR (21,w)<>0 THEN NEXT w
5019 IF w>=30 THEN GO TO 5045
5022 PRINT AT r,w;"{90}"
5031 IF r<=20 THEN PRINT AT r+1,w;" "
5035 IF r=21 THEN BEEP .02,09: BEEP .05,45: BEEP .07,5
5040 NEXT r: NEXT w
5045 PRINT AT 2,29;"  "
5050 PRINT AT x,y;"  ": LET h=4: FOR t=31 TO 0 STEP -1: PRINT AT h,t;"   "
5051 LET h=h+INT (RND*3-1)
5052 INK (RND*7): PLOT BRIGHT 1;INT (RND*255),175-INT (RND*100): INK 7: PRINT AT h,t;"{9D}{9C} ": NEXT t: REM PRINT AT h,t;"  ": REM NEXT t
5053 PRINT AT h,0;"  ": IF i<>27 THEN PAUSE 20: GO TO 94
5055 CLS 
5060 INPUT "Another game ";j$
5070 IF j$<>"y" AND j$<>"n" THEN GO TO 5060
5075 FOR b=0 TO 224: OUT 254,b: NEXT b: PRINT AT 10,14;"OK": PAUSE 150
5080 IF j$="y" THEN RUN 

   4 REM DUNGEONS OF DOOM
   5 REM Character definition
   6 CLS : PRINT "Setting up graphics"
  10 FOR a=1 TO 14: READ a$: FOR b=0 TO 7: READ n: POKE USR a$+b,n: NEXT b: NEXT a
  15 DATA "b",62,126,70,70,70,70,70,124
  20 DATA "c",0,63,67,253,253,254,252,0
  30 DATA "d",6,69,101,118,120,124,126,0
  40 DATA "e",0,62,62,62,58,62,62,62
  50 DATA "f",128,54,28,72,8,10,40,0
  60 DATA "g",0,60,126,0,60,126,0,0
  70 DATA "i",48,39,125,167,32,80,72,72
  80 DATA "k",127,128,158,161,165,153,129,126
  90 DATA "m",90,36,24,60,90,24,36,102
 100 DATA "o",0,24,60,126,60,24,60,126
 110 DATA "p",16,56,124,126,60,28,24,0
 120 DATA "s",0,60,66,90,90,66,60,0
 125 DATA "t",73,20,34,73,34,20,73,0
 130 DATA "u",80,82,114,14,30,62,126,0
 150 PRINT "Would you like a printout of allthe graphic characters..."
 151 PRINT "S=To screen": PRINT "P=To printer": PRINT "N=No - Load game"
 159 INPUT y$
 160 IF y$(1)="p" THEN GO TO 500
 161 IF y$(1)="s" THEN GO TO 700
 162 IF y$(1)="n" THEN GO TO 1000
 170 STOP 
 500 LPRINT "{91}=A book"
 505 LPRINT 
 510 LPRINT "{92}=A chest"
 515 LPRINT 
 520 LPRINT "{94}=The entrance"
 525 LPRINT 
 530 LPRINT "{95}=Flares"
 535 LPRINT 
 540 LPRINT "{96}=Gold"
 545 LPRINT 
 550 LPRINT "{98}=A vendor"
 555 LPRINT 
 560 LPRINT "{9A}=A warp"
 565 LPRINT 
 570 LPRINT "{9C}=A monster"
 575 LPRINT 
 580 LPRINT "{9E}=An orb"
 585 LPRINT 
 590 LPRINT "{9F}=A pool"
 595 LPRINT 
 600 LPRINT "{A2}=A sinkhole"
 605 LPRINT 
 610 LPRINT "{A3}=Treasure"
 615 LPRINT 
 620 LPRINT "{A4}=Stairs up"
 630 STOP 
 700 CLS : PRINT "Graphics:": PRINT 
 701 PRINT "{91}=A book"
 702 PRINT "{92}=A chest"
 703 PRINT "{95}=Flares"
 704 PRINT "{96}=Gold"
 705 PRINT "{98}=A vendor"
 706 PRINT "{9A}=A warp"
 707 PRINT "{9C}=A monster"
 708 PRINT "{9E}=An orb"
 709 PRINT "{9F}=A pool"
 710 PRINT "{A2}=A sinkhole"
 711 PRINT "{A3}=Treasure"
 712 PRINT "{A4}=Stairs up"
 799 PAUSE 0
 800 PRINT : GO TO 150
1000 CLS : PRINT "loading.."
1010 LOAD ""

   1 REM ASTROCRASH
   2 REM by Kevin Ridley '84
   3 REM Typed and fixed by Paul Jenkinsn 2022
   4 REM Original listing had a subroutine mising that setup the arays and UDGs. I had to guess how this may have been.
   5 GO SUB 901
  10 GO SUB 801
  15 GO SUB 701: GO SUB 21: GO SUB 601: IF INKEY$="s" THEN BORDER 7: INK 0: PAPER 7: CLS : STOP 
  17 GO TO 15
  20 REM MAIN
  21 LET i$=INKEY$: IF i$="z" OR i$="x" THEN GO SUB 101: IF p<=0 THEN RETURN 
  22 IF i$=" " THEN GO SUB 151: IF p<=0 THEN RETURN 
  23 IF i$<>CHR$ 13 THEN GO TO 26
  24 GO SUB 201: IF hit THEN GO SUB 401: IF sc>=50 THEN RETURN 
  25 IF p<=0 THEN RETURN 
  26 IF NOT m THEN GO SUB 301
  27 IF m THEN GO SUB 351
  28 IF crash THEN GO SUB 501: IF NOT life OR p<=0 THEN RETURN 
  29 GO TO 21
 100 REM {14}{00}{11}{00}{10}{07}Turn Ship{11}{07} FORMAT {00}{10}{00}
 101 PRINT AT l,c;CHR$ ch
 105 LET ch=ch+((-3 OR ch<147) AND i$="z")-((-3 OR ch>144) AND i$="x")
 115 PRINT AT l,c;CHR$ ch
 120 LET p=p-1: PRINT OVER 0;AT 21,6;p AND p>0
 149 RETURN 
 150 REM Advance Rocket
 151 LET dl=(3-(l-17 AND l>17) AND ch=146)-(3-(3-l AND l<3) AND ch=144)
 155 LET dc=(3-(c-28 AND c>28) AND ch=147)-(3-(3-c AND c<3) AND ch=145)
 157 IF dl=dc THEN RETURN 
 160 PRINT AT l,c; OVER 0;" "
 165 LET l=l+dl: LET c=c+dc
 166 PRINT AT l,c; OVER 0;CHR$ ch
 175 LET p=p-2: PRINT OVER 0;AT 21,6;p AND p>0;" "
 199 RETURN 
 200 REM Fire Laser
 201 LET px=c*8+4: LET py=171-l*8
 205 LET dy=(80-(py-95 AND py>95) AND ch=144)-(80-(88-py AND py<88) AND ch=146)
 210 LET dx=(80-(px-175 AND px>175) AND ch=147)-(80-(80-px AND px<80) AND ch=145)
 225 FOR f=1 TO m
 235 IF dy AND c=c(f) THEN LET ndy=(l-l(f))*8: IF SGN ndy=SGN dy AND ABS ndy<=ABS dy THEN LET hit=f: LET dy=ndy
 240 IF dx AND l=l(f) THEN LET ndx=(c(f)-c)*8: IF SGN ndx=SGN dx AND ABS ndx<=ABS dx THEN LET hit=f: LET dx=ndx
 245 NEXT f
 250 FOR n=1 TO 2
 255 OVER 1: PLOT px,py: DRAW dx,dy: OVER 0
 260 BEEP .05,10*n
 265 NEXT n
 270 LET p=p-5: PRINT OVER 0;AT 21,6;p AND p>0;" "
 299 RETURN 
 300 REM Create Meteors
 301 LET m=1+(sc>5)+(sc>21)
 302 FOR f=1 TO m
 305 IF INT (RND*2) THEN LET l(f)=20*INT (RND*2): LET c(f)=INT (RND*31+.5): GO TO 315
 310 LET l(f)=INT (RND*20+.5): LET c(f)=31*INT (RND*2)
 315 LET d(f)=INT (RND+1.5): LET d(f+3)=INT (RND+1.5)
 320 LET i(f)=6-(4 AND RND>.66)
 325 PRINT INK i(f);AT l(f),c(f);CHR$ 148
 330 IF l(f)=l AND c(f)=c THEN LET crash=1
 335 NEXT f
 349 RETURN 
 350 REM Move Meteors
 351 FOR f=1 TO m
 354 LET ml=l(f): LET mc=c(f)
 356 IF i(f)=6 THEN GO TO 368
 357 LET ld=l-l(f): LET cd=c-c(f)
 358 IF ABS ld<3 AND ABS cd<3 AND (ld OR cd) THEN LET l(f)=l: LET c(f)=c: GO TO 390
 362 IF ld THEN LET d(f)=ABS d(f)*SGN ld
 364 IF cd THEN LET d(f+3)=ABS d(f+3)*SGN cd
 368 LET l(f)=l(f)+d(f): LET c(f)=c(f)+d(f+3)
 370 IF l(f)>=20 THEN LET d(f)=-d(f): LET l(f)=20
 372 IF l(f)<=0 THEN LET d(f)=-d(f): LET l(f)=0
 374 IF c(f)>=31 THEN LET d(f+3)=-d(f+3): LET c(f)=31
 376 IF c(f)<=0 THEN LET d(f+3)=-d(f+3): LET c(f)=0
 380 IF ATTR (l(f),c(f))>64 THEN LET l(f)=ml: LET c(f)=mc: LET d(f)=INT (RND+1.5)*SGN d(f): LET d(f+3)=INT (RND+1.5)*SGN d(f+3): GO TO 356
 390 PRINT PAPER 0; BRIGHT 0; OVER 1; INK 8;AT ml,mc;CHR$ 148
 392 PRINT PAPER 0; INK i(f); BRIGHT 0; OVER 1;AT l(f),c(f);CHR$ 148
 394 IF l(f)=l AND c(f)=c THEN LET crash=1
 396 NEXT f
 399 RETURN 
 400 REM Hit Procedure
 401 LET hl=l(hit)-(l(hit)<>0)-(l(hit)=20)
 402 LET hc=c(hit)-(c(hit)<>0)-(c(hit)=31)
 404 PRINT AT l(hit),c(hit);CHR$ 148
 405 PRINT OVER 1;AT hl,hc+1;"|";AT hl+1,hc;"-{8F}-";AT hl+2,hc+1;"|"
 406 FOR n=9 TO 0 STEP -1
 407 INK n+(9 AND NOT n)
 408 REM PRINT AT hl,hc,"{84}|{88}";AT hl+1,hc;"-{8F}-";AT hl+2,hc;"{81}|{82}"
 409 PRINT OVER 1;AT hl,hc;"{84}|{88}";AT hl+1,hc;"-{8F}-";AT hl+2,hc;"{81}|{82}"
 410 BEEP .005,10+20*(n<5)
 412 NEXT n
 414 PRINT OVER 1;AT hl,hc+1;"|";AT hl+1,hc;"-{8F}-";AT hl+2,hc+1;"|"
 415 PRINT AT hl+1,hc+1;" "
 420 LET sc=sc+1
 425 PRINT OVER 0;AT 21,30;sc
 430 IF hit=m THEN GO TO 498
 435 FOR f=hit TO m-1
 440 LET l(f)=l(f+1): LET c(f)=c(f+1)
 445 LET d(f)=d(f+1): LET d(f+3)=d(f+4)
 450 LET i(f)=i(f+1): NEXT f
 498 LET m=m-1: LET hit=0
 499 RETURN 
 500 REM Crash Procedure
 501 LET crash=0
 502 LET cl=l-(l<>0)-(l=20)
 503 LET cc=c-(c<>0)-(c=31)
 504 PRINT AT l,c;" ";AT l,c;CHR$ ch;AT cl+1,cc+1;"#"
 506 FOR n=1 TO 10: INK n-(n=10)
 508 PRINT AT cl,cc;"{8D} {8E}";AT cl+1,cc;" # ";AT cl+2,cc;"{87} {8B}"
 510 BEEP .005,10+20*(n<6)
 512 NEXT n
 513 PRINT AT cl,cc;"   ";AT cl+2,cc;"   ";AT l,c;CHR$ ch
 514 LET life=life-1: PRINT OVER 0;AT 21,21;life
 520 LET p=p-10: PRINT OVER 0;AT 21,6;p AND p>0;" "
 599 RETURN 
 600 REM End Of Game Procedure
 601 OVER 0: IF sc<50 THEN GO TO 650
 605 FOR n=2 TO 5
 610 BORDER n
 615 PRINT INK n;AT 6,12;"SUCCESS!"
 617 IF n<>5 THEN BEEP .25,11
 618 IF n=5 THEN BEEP 1,7
 620 NEXT n
 625 PRINT AT 8,1;"YOU'VE WON"
 630 GO TO 680
 650 FOR n=5 TO 1 STEP -.5
 655 BORDER n
 660 PRINT INK 6-n;AT 6,12;"FAILURE!"
 662 BEEP .1,(n-5)*10
 665 NEXT n
 670 LET m$=("YOU'RE DEAD" AND NOT life)+("  NO POWER" AND life)
 675 PRINT AT 8,10;m$
 680 PRINT AT 12,2;"Press ""s""to stop, any other";TAB 2;"key to play again"
 685 IF INKEY$="" THEN GO TO 685
 699 RETURN 
 700 REM Draw Scren Initialise Variables
 701 OVER 0: BORDER 1: CLS 
 702 FOR n=1 TO 50
 704 INK RND*6+1
 705 PLOT RND*254,RND*167+8
 708 DRAW RND,0: NEXT n: INK 9
 710 LET life=5: LET p=999: LET sc=0
 711 PRINT PAPER 9;AT 21,0;"POWER:";p;" "
 712 PRINT PAPER 4;AT 21,10;"LIVES LEFT:";life
 714 PRINT PAPER 3;AT 21,22;" SCORE:";sc;" "
 715 LET ch=144: LET l=10: LET c=15
 716 PRINT AT l,c;CHR$ ch
 720 LET m=0: LET hit=0
 722 LET crash=0
 799 RETURN 
 800 REM instructions
 801 BORDER 0: PAPER 0: INK 9: CLS 
 810 PRINT TAB 10; PAPER 1;"*ASTROCRASH*"
 815 PRINT AT 3,3;"Your rocket is in a meteor   storm.  To win you must destroy 50 meteors with your laser.  If your power runs out or your 5   lives are used up, you lose."
 820 PRINT AT 10,3;"Power is used up by turning  the rocket (1 unit), by advanc- ing the rocket (2 units), by    firing the laser (5 units), and by crashing into a meteor (10   units). Crashing also causes 1  life to be lost."
 825 PRINT AT 20,3; FLASH 1;"PRESS ANY KEY TO CONTINUE."
 830 PAUSE 0
 835 CLS : PRINT TAB 3;"The number of meteors on the screen at any one time increasesto a maximum of 3.  the yellow  meteors move randomly but the   red ones are magnetic and thus  home in on the ship."
 840 PRINT AT 8,3;"Control keys:-"
 845 PRINT AT 10,3;"ENTER - Fire laser."
 850 PRINT AT 12,3;"SPACE - Advance rocket."
 852 PRINT AT 14,3;"X";TAB 9;"- Turns ship 90 degrees";TAB 11;"clockwise."
 855 PRINT AT 16,3;"Z";TAB 9;"- Turns ship 90 degrees";TAB 11;"anti-clockwise."
 860 INPUT TAB 3; FLASH 1;"Enter ""y"" to play.";r$
 865 IF r$<>"y" THEN BEEP 1,10: GO TO 860
 899 RETURN 
 900 REM UDG's
 901 DIM l(10): DIM c(10)
 902 DIM d(10): DIM i(10)
 905 RESTORE 
 910 FOR a=USR "A" TO USR "E"+7
 911 READ b
 912 POKE a,b
 913 NEXT a
 920 DATA 24,24,36,189,231,189,165,129
 921 DATA 31,8,62,212,212,62,8,31
 922 DATA 129,165,189,231,189,36,24,24
 923 DATA 248,16,124,43,43,124,16,248
 924 DATA 94,251,111,126,189,191,111,54
 950 RETURN 

  10 REM Spectrum smalltalk
  20 GO SUB 1000
  30 GO SUB 2000
  40 GO SUB 3000
  50 GO SUB 5000
  60 IF num<>0 THEN GO SUB num
  70 GO SUB 9800
  80 GO TO 30
1000 CLS 
1010 PRINT AT 1,2;"Hi! My name is ZX Spectrum"
1030 PRINT 
1040 PRINT "I would like you to talk to me"
1050 PRINT "but I don't have ears so will"
1060 PRINT "you type sentences on my"
1070 PRINT "keyboard"
1074 PRINT 
1075 PRINT "Don't use any punctuation apart"
1076 PRINT "from apostrophies which are"
1078 PRINT "important"
1080 PRINT 
1110 PRINT "When you have finished typing"
1115 PRINT "press ENTER"
1120 PRINT AT 18,0; BRIGHT 1;"Tell me about your problems"
1130 LET r$=""
1140 LET m$=""
1150 LET d$=""
1160 DIM n$(3,32)
1170 LET n$(1)="Please go on"
1180 LET n$(2)="I'm not sure I understand you"
1190 LET n$(3)="Tell me more"
1200 DIM i$(3,40)
1210 LET i$(1)="Let's talk some more about your"
1220 LET i$(2)="Earlier you spoke of your "
1230 LET i$(3)="Does that have anything to do with your "
1235 DIM j$(2,32)
1240 LET j$(1)="Are you just being negative"
1250 LET j$(2)="I see"
1990 RETURN 
2000 LET a$=""
2010 LET b$=INKEY$
2015 POKE 23692,255
2020 IF b$="" THEN GO TO 2010
2025 IF INKEY$<>"" THEN GO TO 2025
2030 IF CODE (b$)=13 THEN GO TO 2200
2040 IF CODE (b$)=12 AND a$<>"" THEN LET a$=a$( TO LEN a$-1): GO TO 2090
2050 IF CODE b$<32 OR CODE b$>126 THEN GO TO 2000
2060 LET a$=a$+b$
2090 PRINT AT 20,0;a$;" "
2100 GO TO 2010
2200 IF a$(LEN a$)=" " THEN LET a$=a$( TO LEN a$-1): GO TO 2200
2202 IF a$=r$ THEN PRINT AT 21,0;"You're repeating  yourself!"'''': GO TO 2000
2203 LET r$=a$
2204 IF a$="" THEN GO TO 2000
2205 LET a$=" "+a$
2215 IF CODE (a$(2))<97 THEN LET a$(2)=CHR$ (CODE a$(2)+32)
2220 PRINT AT 21,0;'''
2230 RETURN 
3000 DIM w(20,2)
3005 LET n=1
3010 LET b=0
3020 FOR i=1 TO LEN a$
3040 IF (a$(i)=" " OR a$(i)=",") AND b=0 THEN LET b=1
3050 IF (a$(i)<>" " OR a$(i)<>",") AND b<=1 THEN LET w(n,1)=i: LET b=2
3060 IF (a$(i)=" " OR a$(i)=",") AND b=2 THEN LET w(n,2)=i-1: LET n=n+1: LET b=0
3070 NEXT i
3080 LET w(n,2)=LEN a$
3600 FOR i=1 TO n
3605 RESTORE 3800
3610 READ b$
3620 IF b$="s" THEN GO TO 3690
3630 IF b$<>a$(w(i,1) TO w(i,2)) THEN GO TO 3680
3640 READ c$
3650 LET a$=a$( TO w(i,1)-1)+c$+a$(w(i,2)+1 TO )
3654 LET w(i,2)=w(i,2)+LEN c$-LEN b$
3655 FOR j=i+1 TO n
3660 LET w(j,2)=w(j,2)+LEN c$-LEN b$
3664 LET w(j,1)=w(j,1)+LEN c$-LEN b$
3665 NEXT j
3670 GO TO 3690
3680 READ b$
3685 GO TO 3610
3690 NEXT i
3700 RETURN 
3800 DATA "my","your*","I","you*","i","you*"
3810 DATA "mum","Mother","dad","Father"
3820 DATA "dreams","dream","you","I*","me","you*"
3830 DATA "your","my*","myself","yourself*","I'm","you're"
3840 DATA "yourself","myself*","I'm","you're*"
3850 DATA "you're","I'm*","am","are*"
3870 DATA "i'm","you're*"
3880 DATA "were","was"
3885 DATA "are","am"
3890 DATA "s","s"
5000 RESTORE 6000
5010 READ b$,num
5020 IF b$="s" THEN GO TO 5710
5025 FOR i=1 TO n
5030 IF a$(w(i,1) TO w(i,2))<>b$ THEN GO TO 5700
5040 LET t$=a$(w(i,2)+1 TO )
5050 RETURN 
5700 NEXT i
5705 GO TO 5010
5710 LET num=0
5720 IF m$<>"" THEN GO TO 5800
5730 LET p$=n$(INT (RND*3)+1)
5740 RETURN 
5800 LET p$=i$(INT (RND*3)+1)+m$
5900 RETURN 
6000 DATA "computer",7000,"machine",7000
6010 DATA "like",7100,"same",7100,"alike",7100
6020 DATA "if",7200,"everybody",7300
6024 DATA "can",8200,"certainly",8250
6025 DATA "how",8100,"because",8150
6026 DATA "always",7800
6030 DATA "everyone",7300,"nobody",7300
6034 DATA "was",7500
6035 DATA "I*",8800
6040 DATA "no",7400
6060 DATA "your*",7600
6070 DATA "you're*",8500,"you*",8650
6110 DATA "hello",8300,"maybe",8350
6120 DATA "my*",8370,"no",8420
6130 DATA "yes",8250,"why",8450
6140 DATA "perhaps",8350,"sorry",8400
6160 DATA "what",8450
6900 DATA "s",0
7000 LET p$="Do computers worry you?"
7010 RETURN 
7100 LET p$="In what way ?"
7110 RETURN 
7200 LET p$="Why talk of possibilities"
7210 RETURN 
7300 LET p$="Really "+b$+" ?"
7310 RETURN 
7400 IF i=n THEN GO TO 7450
7410 LET i=i+1
7420 IF a$(w(i,1) TO w(i,2))="one" THEN LET b$=b$+" one": GO TO 7300
7450 LET p$=j$(INT (RND*2)+1)
7460 RETURN 
7500 IF i=n THEN GO TO 9900
7510 LET i=i+1
7515 IF i>n THEN GO TO 5720
7520 IF a$(w(i,1) TO w(i,2))<>"you*" THEN GO TO 7550
7530 LET p$="What if you were "+a$(w(i,2)+1 TO )+" ?"
7540 RETURN 
7550 IF a$(w(i,1) TO w(i,2))<>"I*" THEN GO TO 5720
7560 LET p$="Would you like to believe I was "+a$(w(i,2)+1 TO )
7570 RETURN 
7600 LET i=i+1
7605 IF i>n THEN GO TO 7450
7610 IF a$(w(i,1) TO w(i,2))="Mother" THEN GO TO 7700
7620 IF a$(w(i,1) TO w(i,2))="Father" THEN GO TO 7700
7630 IF a$(w(i,1) TO w(i,2))="sister" THEN GO TO 7700
7640 IF a$(w(i,1) TO w(i,2))="brother" THEN GO TO 7700
7650 IF a$(w(i,1) TO w(i,2))="wife" THEN GO TO 7700
7660 IF a$(w(i,1) TO w(i,2))="husband" THEN GO TO 7700
7670 IF a$(w(i,1) TO w(i,2))="children" THEN GO TO 7700
7680 IF LEN t$>10 THEN LET m$=t$
7690 LET p$="your "+t$+" ?"
7695 RETURN 
7700 LET p$="Tell me more about your family"
7710 RETURN 
7800 LET p$="Give me a particular example"
7810 RETURN 
7900 LET i=i+1
7905 IF i>n THEN LET p$="Am I what ?": RETURN 
7920 LET p$="Why are you interested in whether I am "+a$(w(i,1) TO )+" or not?"
7930 RETURN 
8000 LET p$="Do you think you are "+a$(w(i,2) TO )
8030 RETURN 
8100 LET p$="Why do you ask ?"
8110 RETURN 
8150 LET p$="Tell me about any other reasons"
8160 RETURN 
8200 LET i=i+1
8205 IF i>n THEN LET p$="What ?": RETURN 
8210 IF a$(w(i,1) TO w(i,2))="I*" THEN LET p$="Do you believe I can "+a$(w(i,2)+1 TO )+" ?": RETURN 
8220 IF a$(w(i,1) TO w(i,2))="you*" THEN LET p$="Do you believe you can "+a$(w(i,2)+1 TO )+" ?": RETURN 
8230 GO TO 5720
8250 LET p$="You seem very positive"
8260 RETURN 
8300 LET p$="Pleased to meet you - let's talk about your problems"
8310 RETURN 
8350 LET p$="Could you try to be more positive"
8360 RETURN 
8370 LET p$="Why are yo concerned about my "+t$
8380 RETURN 
8400 LET p$="You don't have to apologise to me"
8410 RETURN 
8450 LET p$="Some questions are difficult to answer..."
8460 RETURN 
8500 LET i=i+1
8505 IF i>n THEN GO TO 5720
8510 LET p$="I am sorry to hear that you are "+a$(w(i,1) TO w(i,2))
8520 IF a$(w(i,1) TO w(i,2))="sad" THEN RETURN 
8530 IF a$(w(i,1) TO w(i,2))="unhappy" THEN RETURN 
8540 IF a$(w(i,1) TO w(i,2))="depressed" THEN RETURN 
8550 IF a$(w(i,1) TO w(i,2))="sick" THEN RETURN 
8560 LET p$="How have I helped you to be "+a$(w(i,1) TO w(i,2))
8570 IF a$(w(i,1) TO w(i,2))="happy" THEN RETURN 
8580 IF a$(w(i,1) TO w(i,2))="elated" THEN RETURN 
8590 IF a$(w(i,1) TO w(i,2))="glad" THEN RETURN 
8600 IF a$(w(i,1) TO w(i,2))="better" THEN RETURN 
8610 LET p$="Is it because you are "+a$(w(i,1) TO )+" you would like to talk to me ?"
8620 RETURN 
8650 IF i=1 THEN GO TO 8660
8654 IF a$(w(i-1,1) TO w(i-1,2))="are*" THEN GO TO 8000
8655 LET i=i+1
8656 IF i>n THEN GO TO 9900
8660 IF a$(w(i,1) TO w(i,2))="are*" THEN GO TO 8500
8670 IF a$(w(i,1) TO w(i,2))="want" OR a$(w(i,1) TO w(i,2))="need" THEN LET p$="what would it mean if you got "+a$(w(i,2)+1 TO ): RETURN 
8675 IF a$(w(i,1) TO w(i,2))="think" THEN LET p$="do you really think so": RETURN 
8680 IF a$(w(i,1) TO w(i,2))="can't" OR a$(w(i,1) TO w(i,2))="cannot" THEN LET p$="How do you think you can't "+a$(w(i,2)+1 TO ): RETURN 
8690 IF a$(w(i,1) TO w(i,2))="feel" THEN LET p$="tell me more about how you feel": RETURN 
8700 GO TO 5720
8800 IF i-1<1 THEN GO TO 8805
8804 IF a$(w(i,1) TO w(i,2))="am" THEN GO TO 7900
8805 LET i=i+1
8810 IF i>=n THEN LET p$="What am I ?": RETURN 
8820 IF a$(w(i,1) TO w(i,2))="am" THEN LET p$="Why do you think so ?": RETURN 
8830 LET p$="Is that what you think of me !"
8840 RETURN 
9800 FOR j=1 TO LEN p$
9810 IF p$(j)<>"*" THEN PRINT BRIGHT 1;p$(j);
9820 NEXT j
9830 PRINT AT 21,0''''
9840 RETURN 
9900 LET p$="Please talk sensibly !"
9910 RETURN 

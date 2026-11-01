  10 FOR f=USR "a" TO USR "a"+9
  20 READ a: POKE f,a: NEXT f
  30 DATA 33,0,0,17,0,0,205,181,3,201
  35 POKE USR "a"+1,80: REM this number can be changed to alter the tone
  40 GO SUB 50: PAUSE 13: GO SUB 50: PAUSE 75: GO TO 40
  50 FOR f=0 TO 10: POKE USR "a"+4,10: RANDOMIZE USR USR "a": POKE USR "a"+4,1: RANDOMIZE USR USR "a": NEXT f: RETURN 

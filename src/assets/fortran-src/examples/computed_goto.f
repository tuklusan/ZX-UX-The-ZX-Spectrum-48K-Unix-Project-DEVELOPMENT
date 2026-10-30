      PROGRAM CGOTO
      INTEGER SEL, VALUE
      SEL = 2
      GO TO (10,20,30), SEL
      VALUE = -1
      GO TO 40
   10 VALUE = 11
      GO TO 40
   20 VALUE = 22
      GO TO 40
   30 VALUE = 33
   40 WRITE (6,100) VALUE
      SEL = 7
      GOTO (50,60), SEL
      VALUE = 44
      GO TO 70
   50 VALUE = -5
      GO TO 70
   60 VALUE = -6
   70 WRITE (6,100) VALUE
  100 FORMAT (I4)
      END

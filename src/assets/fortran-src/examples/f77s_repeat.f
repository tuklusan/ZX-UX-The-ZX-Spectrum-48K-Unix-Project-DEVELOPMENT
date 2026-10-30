      PROGRAM REPT
      INTEGER A,B,C,S
      READ(5,10) A,B,C
   10 FORMAT(2(I3,1X),I3)
      S=A+B+C
      WRITE(6,20) A,B,C,S
   20 FORMAT(3(I3,1X),I4)
      END

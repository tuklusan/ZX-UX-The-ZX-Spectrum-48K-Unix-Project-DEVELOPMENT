      PROGRAM EXPOUT
      REAL A,B,C,D,E,F
      A=12.34
      B=-0.0125
      C=0.0
      D=1.0
      E=100.0
      F=-0.0000123
      WRITE (6,10) A,B
      WRITE (6,11) C
      WRITE (6,11) D
      WRITE (6,11) E
      WRITE (6,11) F
   10 FORMAT(2E14.6)
   11 FORMAT(E14.6)
      END

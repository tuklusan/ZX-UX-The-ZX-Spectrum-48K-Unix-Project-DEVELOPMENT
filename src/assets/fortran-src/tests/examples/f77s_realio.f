C     Restricted F77S formatted REAL input and output.
      PROGRAM RIO
      REAL A,B,C(2)
      DATA A/12.5/,C/0.25,-1.75/
      WRITE(6,10) A
      READ(5,20) B
      WRITE(6,10) B
      WRITE(6,30) C(1),C(2)
      READ(5,20) B
      WRITE(6,10) B
   10 FORMAT(F8.2)
   20 FORMAT(F8.2)
   30 FORMAT(2F8.2)
      END

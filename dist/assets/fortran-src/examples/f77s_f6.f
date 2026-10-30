C     Six-decimal F output and input with sign/rounding tests.
      PROGRAM PREC6
      REAL A,B,C
      A=1.234567
      B=-0.000125
      C=9.999999
      WRITE(6,10) A,B,C
   10 FORMAT(3F12.6)
      READ(5,20) A,B,C
   20 FORMAT(3F12.6)
      WRITE(6,10) A,B,C
      END

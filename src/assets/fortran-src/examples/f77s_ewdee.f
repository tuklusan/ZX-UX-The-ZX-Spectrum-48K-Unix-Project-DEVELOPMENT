C     E data output with an explicit exponent digit count.
      PROGRAM EWDIG
      REAL A,B,C
      A=123.4
      B=0.0125
      C=-0.0000123
      WRITE(6,10) A,B,C
   10 FORMAT(E16.6E3,1X,E16.6E3,1X,E16.6E3)
      END

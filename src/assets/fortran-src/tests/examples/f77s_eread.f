C     Decimal and signed exponent E input, fixed record widths.
      PROGRAM EREAD
      REAL A,B
      READ(5,10) A,B
   10 FORMAT(E16.6E3,E16.6E3)
      WRITE(6,20) A,B
   20 FORMAT(2F9.2)
      END

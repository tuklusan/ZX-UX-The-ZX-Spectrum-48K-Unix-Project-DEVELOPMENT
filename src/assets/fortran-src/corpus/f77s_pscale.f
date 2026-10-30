C     F77S P scale with F input and output, then scale reset.
      PROGRAM PSCAL
      REAL A,B
      A=1.23
      B=1.23
      WRITE(6,10) A,B
   10 FORMAT(1P,F8.2,0P,F8.2)
      READ(5,20) A,B
   20 FORMAT(1P,F8.2,0P,F8.2)
      WRITE(6,30) A,B
   30 FORMAT(2F8.2)
      END

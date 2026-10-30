C     F77S P scale with E output and E input.
      PROGRAM ESCALE
      REAL A,B
      A=290.0
      WRITE(6,10) A
   10 FORMAT(2P,E9.3)
      WRITE(6,20) A
   20 FORMAT(1P,E9.3)
      WRITE(6,30) A
   30 FORMAT(-1P,E9.3)
      READ(5,40) B
   40 FORMAT(3P,E8.2)
      WRITE(6,50) B
   50 FORMAT(F8.4)
      END

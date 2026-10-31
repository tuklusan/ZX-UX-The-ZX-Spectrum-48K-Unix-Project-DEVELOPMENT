C     Runtime implied DO with E-format real numeric edits.
      PROGRAM VEIO
      REAL A(2)
      INTEGER I,N
      N=2
      READ(5,10) (A(I),I=1,N)
   10 FORMAT(E16.6E3)
      WRITE(6,20) (A(I),I=1,N)
   20 FORMAT(E16.6E3)
      END

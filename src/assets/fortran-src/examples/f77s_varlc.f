C     Runtime implied DO of LOGICAL and CHARACTER array input/output.
      PROGRAM VLOGC
      LOGICAL L(3)
      CHARACTER*3 C(3)
      INTEGER I,N
      N=3
      READ(5,10) (L(I),I=1,N)
   10 FORMAT(2L3)
      READ(5,20) (C(I),I=1,N)
   20 FORMAT(2A3)
      WRITE(6,30) (L(I),I=1,N)
   30 FORMAT(2L4)
      WRITE(6,40) (C(I),I=1,N)
   40 FORMAT(2A3)
      END

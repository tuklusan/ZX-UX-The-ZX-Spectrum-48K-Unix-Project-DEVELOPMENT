C     Rightmost nested FORMAT group receives reversion after records.
      PROGRAM NESTRV
      INTEGER A(10),I
      READ(5,10) (A(I),I=1,10)
   10 FORMAT(I3,2(I4,I5))
      WRITE(6,10) (A(I),I=1,10)
      END

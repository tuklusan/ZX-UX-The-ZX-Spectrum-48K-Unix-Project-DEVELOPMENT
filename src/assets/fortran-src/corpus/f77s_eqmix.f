C     Mixed numeric EQUIVALENCE uses target-safe typed mirrors.
      PROGRAM EQMX
      INTEGER I
      REAL R
      EQUIVALENCE (I,R)
      I=42
      WRITE(6,10) I
   10 FORMAT(I4)
      R=R
      WRITE(6,10) I
      END

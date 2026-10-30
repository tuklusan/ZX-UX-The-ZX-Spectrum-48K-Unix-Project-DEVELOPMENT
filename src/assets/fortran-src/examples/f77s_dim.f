      PROGRAM DIMT
      INTEGER I,J
      DIMENSION K(2,3)
      I=2
      J=3
      K(I,J)=42
      WRITE(6,10) K(2,3)
   10 FORMAT(I4)
      END

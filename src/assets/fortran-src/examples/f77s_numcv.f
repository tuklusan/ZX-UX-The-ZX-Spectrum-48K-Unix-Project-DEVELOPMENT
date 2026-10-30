C     Subset numeric conversions and INTEGER abs on 16-bit target.
      PROGRAM NUMCV
      INTEGER I,J,K,L
      REAL X,Y,Z
      I=-321
      J=IABS(I)
      K=NINT(-2.5)
      L=IFIX(-2.9)
      X=FLOAT(J)
      Y=AINT(-3.8)
      Z=ABS(-3.25)
      WRITE(6,10) J,K,L
   10 FORMAT(3I6)
      WRITE(6,20) X,Y,Z
   20 FORMAT(3F9.2)
      END

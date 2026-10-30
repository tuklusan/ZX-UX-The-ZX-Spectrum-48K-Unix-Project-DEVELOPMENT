      PROGRAM DMRL
      REAL A(2)
      INTEGER K
      A(1)=1.0
      A(2)=2.5
      CALL SCALE(A)
      K=0
      IF (A(2) .EQ. 5.0) K=42
      WRITE(6,10) K
   10 FORMAT(I4)
      END
      SUBROUTINE SCALE(X)
      REAL X(2)
      X(2)=X(2)*2.0
      RETURN
      END

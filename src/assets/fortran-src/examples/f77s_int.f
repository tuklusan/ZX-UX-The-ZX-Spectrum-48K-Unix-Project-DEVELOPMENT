C     F77S INT truncates REAL toward zero, not floor or nearest.
      PROGRAM INTRN
      INTEGER I,J,K,L,M
      REAL X(3),Y
      DATA X/3.9,-3.9,0.75/
      I=INT(X(1))
      J=INT(X(2))
      K=INT(X(3))
      L=INT(-X(3))
      Y=-2.8
      M=INT(Y+0.3)
      WRITE(6,10) I,J,K,L,M
   10 FORMAT(5I6)
      END

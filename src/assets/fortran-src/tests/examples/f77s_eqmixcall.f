C     Mixed numeric EQUIVALENCE write-back after a by-reference call.
      PROGRAM EQMC
      INTEGER I
      REAL R
      EQUIVALENCE (I,R)
      I=42
      CALL SETI(I)
      WRITE(6,10) I
   10 FORMAT(I4)
      END
      SUBROUTINE SETI(X)
      INTEGER X
      X=43
      END

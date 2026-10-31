C     Initialized local DATA used by a called F77S subroutine.
      PROGRAM SBDATA
      INTEGER X
      X=0
      CALL DATASB(X)
      WRITE(6,10) X
      X=0
      CALL DATASB(X)
      WRITE(6,10) X
   10 FORMAT(I4)
      END
      SUBROUTINE DATASB(X)
      INTEGER X,N
      DATA N/40/
      X=N+2
      RETURN
      END

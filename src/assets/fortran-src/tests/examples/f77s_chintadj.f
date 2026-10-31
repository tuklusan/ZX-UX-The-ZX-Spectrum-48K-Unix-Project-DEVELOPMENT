C     Adjustable CHARACTER array used as a multi-record internal file.
      PROGRAM CHIA
      CHARACTER*10 A(2)
      INTEGER I,J
      CALL MAKE(2,A)
      READ(A,10) I,J
      WRITE(6,20) I,J
   10 FORMAT(2I5)
   20 FORMAT(2I5)
      END
      SUBROUTINE MAKE(N,B)
      INTEGER N,X,Y
      CHARACTER*10 B(N)
      X=12
      Y=34
      WRITE(B,10) X,Y
   10 FORMAT(2I5)
      END

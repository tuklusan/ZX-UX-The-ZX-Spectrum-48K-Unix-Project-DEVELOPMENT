C     Adjustable/assumed-size whole-array formatted READ and WRITE.
      PROGRAM WADJ
      INTEGER A(4)
      A(1)=1
      A(2)=2
      A(3)=3
      A(4)=4
      CALL OUT(A,4)
      CALL IN(A,4)
      CALL OUT(A,4)
      END
      SUBROUTINE OUT(X,N)
      INTEGER N,X(N)
      WRITE(6,10) X
   10 FORMAT(4I4)
      END
      SUBROUTINE IN(X,N)
      INTEGER N,X(*)
      READ(5,10) X
   10 FORMAT(4I4)
      END

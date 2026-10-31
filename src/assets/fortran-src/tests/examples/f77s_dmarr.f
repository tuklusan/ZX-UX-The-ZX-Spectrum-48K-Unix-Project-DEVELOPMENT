      PROGRAM DMARR
      INTEGER A(2,3),I,J
      DO 10 J=1,3
      DO 10 I=1,2
      A(I,J)=5
   10 CONTINUE
      CALL UPDATE(A)
      WRITE(6,30) A(1,2)
   30 FORMAT(I4)
      END
      SUBROUTINE UPDATE(X)
      INTEGER X(6)
      X(3)=X(3)+35
      RETURN
      END

C     Variable leading INTEGER dummy array bound with fixed final extent.
      PROGRAM LEAD
      INTEGER A(2,3),N,X
      DATA A/1,2,3,4,5,6/
      N=2
      CALL ALTER(N,A,X)
      WRITE(6,10) X,A(2,3)
   10 FORMAT(2I5)
      END
      SUBROUTINE ALTER(N,B,X)
      INTEGER N,B(N,3),X
      X=B(2,3)
      B(2,3)=42
      END

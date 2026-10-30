C     Adjustable dummy array leading bound from named COMMON, not dummy.
      PROGRAM CBND
      INTEGER M,A(2,3),X
      COMMON /SIZE/ M
      DATA A/1,2,3,4,5,6/
      M=2
      CALL ALTER(A,X)
      WRITE(6,10) X,A(2,3)
   10 FORMAT(2I5)
      END
      SUBROUTINE ALTER(B,X)
      INTEGER N,B(N,3),X
      COMMON /SIZE/ N
      X=B(2,3)
      B(2,3)=42
      END

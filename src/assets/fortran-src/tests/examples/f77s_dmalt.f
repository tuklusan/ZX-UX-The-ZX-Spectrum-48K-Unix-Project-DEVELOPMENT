C     F77S adjustable 1D dummy with separate DIMENSION statement.
      PROGRAM DMALT
      INTEGER N,A(4)
      DATA A/2,4,6,8/
      N=4
      CALL SCLARR(N,A)
      WRITE(6,10) A(4)
   10 FORMAT(I4)
      END
      SUBROUTINE SCLARR(N,B)
      INTEGER N,B,I
      DIMENSION B(N)
      DO 20 I=1,N
      B(I)=B(I)+1
   20 CONTINUE
      RETURN
      END

C     F77S adjustable last bound in column-major 2D dummy.
      PROGRAM DM2AD
      INTEGER A(2,3),N
      DATA A/1,2,3,4,5,6/
      N=3
      CALL CHANG2(N,A)
      WRITE(6,10) A(1,3)
   10 FORMAT(I4)
      END
      SUBROUTINE CHANG2(N,B)
      INTEGER N,B(2,N)
      B(1,3)=B(1,3)+37
      RETURN
      END

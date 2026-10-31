C     F77S adjustable last bound in column-major 3D dummy.
      PROGRAM DM3AD
      INTEGER A(2,2,2),N
      DATA A/1,2,3,4,5,6,7,8/
      N=2
      CALL CHANG3(N,A)
      WRITE(6,10) A(2,2,2)
   10 FORMAT(I4)
      END
      SUBROUTINE CHANG3(N,B)
      INTEGER N,B(2,2,N)
      B(2,2,2)=B(2,2,2)+34
      RETURN
      END

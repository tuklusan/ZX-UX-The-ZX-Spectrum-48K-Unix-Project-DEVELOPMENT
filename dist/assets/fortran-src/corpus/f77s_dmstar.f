C     F77S assumed-size INTEGER dummy array A(*).
      PROGRAM DMSTAR
      INTEGER A(4)
      DATA A/2,4,6,8/
      CALL MODIFY(A(3))
      WRITE(6,10) A(4)
   10 FORMAT(I4)
      END
      SUBROUTINE MODIFY(B)
      INTEGER B(*)
      B(2)=B(2)+30
      RETURN
      END

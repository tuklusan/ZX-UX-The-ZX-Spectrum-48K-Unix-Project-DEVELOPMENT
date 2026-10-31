C     F77S assumed-size third dimension checked against caller.
      PROGRAM DM3ST
      INTEGER A(2,2,2)
      DATA A/1,2,3,4,5,6,7,8/
      CALL CHAST3(A)
      WRITE(6,10) A(2,2,2)
   10 FORMAT(I4)
      END
      SUBROUTINE CHAST3(B)
      INTEGER B(2,2,*)
      B(2,2,2)=B(2,2,2)+34
      RETURN
      END

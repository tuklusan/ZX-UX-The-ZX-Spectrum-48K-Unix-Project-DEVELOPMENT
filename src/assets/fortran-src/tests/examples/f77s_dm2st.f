C     F77S assumed-size second dimension with checked capacity.
      PROGRAM DM2ST
      INTEGER A(2,3)
      DATA A/1,2,3,4,5,6/
      CALL CHAST2(A)
      WRITE(6,10) A(2,3)
   10 FORMAT(I4)
      END
      SUBROUTINE CHAST2(B)
      INTEGER B(2,*)
      B(2,3)=B(2,3)+36
      RETURN
      END

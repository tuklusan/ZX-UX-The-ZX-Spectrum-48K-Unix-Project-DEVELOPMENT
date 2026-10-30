C     Dynamic element actual sequence for fixed-size dummy array.
      PROGRAM DMIDX
      INTEGER A(5),I
      DATA A/1,2,3,4,5/
      I=3
      CALL ADDSEQ(A(I))
      WRITE(6,10) A(4)
   10 FORMAT(I4)
      END
      SUBROUTINE ADDSEQ(B)
      INTEGER B(3)
      B(2)=B(2)+38
      RETURN
      END

C     F77S element actual storage sequence starts at A(3).
      PROGRAM DMSEQ
      INTEGER A(5)
      DATA A/1,2,3,4,5/
      CALL ADDSEQ(A(3))
      WRITE(6,10) A(4)
   10 FORMAT(I4)
      END
      SUBROUTINE ADDSEQ(B)
      INTEGER B(3)
      B(2)=B(2)+38
      RETURN
      END

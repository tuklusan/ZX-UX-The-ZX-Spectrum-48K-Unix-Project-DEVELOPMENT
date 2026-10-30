      PROGRAM DMCHN
      INTEGER A(3)
      A(1)=3
      A(2)=5
      A(3)=7
      CALL STEP1(A)
      WRITE(6,10) A(2)
   10 FORMAT(I4)
      END
      SUBROUTINE STEP1(A)
      INTEGER A(3)
      CALL STEP2(A)
      RETURN
      END
      SUBROUTINE STEP2(B)
      INTEGER B(3)
      B(2)=B(2)*6
      RETURN
      END

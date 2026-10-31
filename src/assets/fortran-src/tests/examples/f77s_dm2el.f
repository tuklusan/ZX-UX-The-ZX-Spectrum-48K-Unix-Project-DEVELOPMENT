C     Column-major rank-2 variable element actual sequence test.
      PROGRAM DM2EL
      INTEGER A(2,3),I,J
      DATA A/1,2,3,4,5,6/
      I=2
      J=2
      CALL SETSEQ(A(I,J))
      WRITE(6,10) A(2,3),A(1,3)
   10 FORMAT(2I4)
      END
      SUBROUTINE SETSEQ(B)
      INTEGER B(3)
      B(3)=42
      RETURN
      END

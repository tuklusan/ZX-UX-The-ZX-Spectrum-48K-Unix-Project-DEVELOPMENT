C     Column-major rank-3 variable element actual sequence test.
      PROGRAM DM3EL
      INTEGER A(2,2,3),I,J,K
      DATA A/1,2,3,4,5,6,7,8,9,10,11,12/
      I=2
      J=1
      K=2
      CALL SETSEQ(A(I,J,K))
      WRITE(6,10) A(1,1,3),A(2,1,3),A(2,2,2)
   10 FORMAT(3I4)
      END
      SUBROUTINE SETSEQ(B)
      INTEGER B(4)
      B(4)=42
      RETURN
      END

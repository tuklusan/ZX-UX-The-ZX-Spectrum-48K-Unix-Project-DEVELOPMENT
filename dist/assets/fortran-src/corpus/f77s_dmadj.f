C     F77S adjustable INTEGER dummy A(N) with element sequence.
      PROGRAM DMADJ
      INTEGER A(5),N
      DATA A/1,2,3,4,5/
      N=3
      CALL ADJUST(N,A(3))
      WRITE(6,10) A(4)
   10 FORMAT(I4)
      END
      SUBROUTINE ADJUST(N,B)
      INTEGER N,B(N)
      B(2)=B(2)+38
      RETURN
      END

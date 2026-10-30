      PROGRAM SAVET
      INTEGER N
      COMMON /FLAG/ N
      SAVE /FLAG/
      N=41
      CALL INCR()
      WRITE(6,10) N
   10 FORMAT(I4)
      END
      SUBROUTINE INCR()
      INTEGER X
      COMMON /FLAG/ X
      SAVE /FLAG/
      X=X+1
      RETURN
      END

      PROGRAM CMNT
      INTEGER N
      COMMON /BLK/ N
      N=21
      CALL DBL()
      WRITE(6,10) N
   10 FORMAT(I4)
      END
      SUBROUTINE DBL()
      INTEGER X
      COMMON /BLK/ X
      X=2*X
      RETURN
      END

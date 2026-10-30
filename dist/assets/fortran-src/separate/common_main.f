C     Main defines COMMON storage for independently linked subroutine.
      PROGRAM CMAIN
      INTEGER N
      COMMON /BLK/ N
      N=40
      CALL ADD2()
      WRITE(6,10) N
   10 FORMAT(I4)
      END

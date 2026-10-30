      PROGRAM FMTWR
      INTEGER N
      N = 42
      WRITE (6,100) N
      N = -4
      WRITE (6,100) N
      N = 12345
      WRITE (6,100) N
  100 FORMAT ('N=',I4)
      END

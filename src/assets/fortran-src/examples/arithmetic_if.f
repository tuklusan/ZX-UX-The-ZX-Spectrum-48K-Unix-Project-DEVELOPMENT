      PROGRAM ARITH
      INTEGER N, RESULT
      N = -3
      IF (N) 10,20,30
   10 RESULT = 11
      GO TO 40
   20 RESULT = 22
      GO TO 40
   30 RESULT = 33
   40 WRITE (6,200) RESULT
      N = 0
      IF (N) 50,60,70
   50 RESULT = 44
      GO TO 80
   60 RESULT = 55
      GO TO 80
   70 RESULT = 66
   80 WRITE (6,200) RESULT
      N = 2
      IF (N) 90,100,110
   90 RESULT = 77
      GO TO 120
  100 RESULT = 88
      GO TO 120
  110 RESULT = 99
  120 WRITE (6,200) RESULT
  200 FORMAT (I4)
      END

      PROGRAM ARRAYS
      INTEGER NUMS(5), I, S
      S = 0
      DO 100 I = 1, 5
      NUMS(I) = I * I
      S = S + NUMS(I)
  100 CONTINUE
      PRINT *, S
      END

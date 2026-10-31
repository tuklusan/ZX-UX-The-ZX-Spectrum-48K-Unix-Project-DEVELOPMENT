      PROGRAM NEST
      INTEGER I, J, SUM
      SUM = 0
      DO 100 I = 1, 3
        DO 100 J = 1, 2
          SUM = SUM + I * J
  100 CONTINUE
      PRINT *, SUM
      END

C     Fixed-bound CHARACTER array element formatted input.
      PROGRAM ARREAD
      CHARACTER*3 A(2)
      DATA A/'NO','NO'/
      READ(5,10) A(2)
      WRITE(6,20) A(1),A(2)
   10 FORMAT(A3)
   20 FORMAT(2A3)
      END

C     Scalar INTEGER console-unit variables for formatted input/output.
      PROGRAM UNITV
      INTEGER INU,OUTU,N
      INU=5
      OUTU=6
      READ(INU,10) N
   10 FORMAT(I4)
      WRITE(OUTU,20) N
   20 FORMAT(I5)
      END

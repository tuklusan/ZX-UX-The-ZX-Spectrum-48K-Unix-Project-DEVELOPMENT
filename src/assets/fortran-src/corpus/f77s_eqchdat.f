C     CHARACTER DATA storage associated by EQUIVALENCE survives calls.
      PROGRAM EQCD
      CHARACTER*3 X,Y
      CALL STEP(X)
      CALL STEP(Y)
      WRITE(6,10) X,Y
   10 FORMAT(A3,1X,A3)
      END
      SUBROUTINE STEP(OUT)
      CHARACTER*3 OUT,A(2),B
      EQUIVALENCE (A(2),B)
      DATA A/'AA','BB'/
      OUT=B
      B='CC'
      END

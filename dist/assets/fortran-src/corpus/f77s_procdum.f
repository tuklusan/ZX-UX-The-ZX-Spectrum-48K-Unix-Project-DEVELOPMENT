C     F77S REAL external function passed as a procedure argument.
      PROGRAM PCALL
      REAL X,Y,Z
      EXTERNAL SQR,DBL
      X=3.0
      CALL APPLY(SQR,X,Y)
      CALL APPLY(DBL,X,Z)
      WRITE(6,10) Y,Z
   10 FORMAT(2F8.2)
      END
      SUBROUTINE APPLY(F,X,Y)
      REAL F,X,Y
      EXTERNAL F
      Y=F(X)
      END
      REAL FUNCTION SQR(T)
      REAL T
      SQR=T*T
      END
      REAL FUNCTION DBL(T)
      REAL T
      DBL=T+T
      END

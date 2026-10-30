C     EXTERNAL specific procedure and INTRINSIC REAL SIN declaration.
      PROGRAM EXIN
      REAL X,Y,DOUBLE
      EXTERNAL DOUBLE
      INTRINSIC SIN
      X=0.5
      Y=DOUBLE(X)+SIN(X)
      WRITE(6,10) Y
   10 FORMAT(F9.2)
      END
      REAL FUNCTION DOUBLE(X)
      REAL X
      DOUBLE=X*2.0
      END

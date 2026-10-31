C     Unprefixed FUNCTION result type inferred as REAL (S name).
      PROGRAM BAREFN
      REAL X,Y
      X=3.0
      Y=SQUARE(X)
      WRITE(6,10) Y
   10 FORMAT(F8.2)
      END
      FUNCTION SQUARE(X)
      REAL X
      SQUARE=X*X
      END

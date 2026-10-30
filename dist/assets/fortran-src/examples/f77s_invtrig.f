C     Specific trigonometric functions using target C48 math library.
      PROGRAM INVT
      REAL X,A,B,C,D,E
      X=0.5
      A=ASIN(X)
      B=ACOS(X)
      C=ATAN(X)
      D=TAN(X)
      E=ALOG10(100.0)
      WRITE(6,10) A,B,C,D,E
   10 FORMAT(5F9.4)
      END

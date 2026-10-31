C     F77S REAL specific math intrinsics: fixed, portable demo data.
      PROGRAM TRIG
      REAL X,A,B,C,D,E
      X=0.5
      A=SIN(X)
      B=COS(X)
      C=EXP(X)
      D=LOG(C)
      E=SIN(-X)
      WRITE(6,10) A,B,C,D,E
   10 FORMAT(5F9.2)
      END

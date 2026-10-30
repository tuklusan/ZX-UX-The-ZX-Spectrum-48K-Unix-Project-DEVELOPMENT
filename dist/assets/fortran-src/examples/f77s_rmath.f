C     Two-REAL specific ATAN2/AMOD intrinsic domains and quadrant.
      PROGRAM RMFUN
      REAL A,B,C,D,E
      A=ATAN2(1.0,-1.0)
      B=ATAN2(-1.0,-1.0)
      C=AMOD(7.5,2.0)
      D=AMOD(-7.5,2.0)
      E=ATAN2(1.0,0.0)
      WRITE(6,10) A,B,C,D,E
   10 FORMAT(5F9.4)
      END

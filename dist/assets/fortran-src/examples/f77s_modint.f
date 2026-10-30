C     Valid signed MOD operands: target 16-bit INTEGER boundaries.
      PROGRAM MODINT
      INTEGER A,B,C,D
      A=MOD(17,5)
      B=MOD(-17,5)
      C=MOD(17,-5)
      D=MOD(-32768,7)
      WRITE(6,10) A,B,C,D
   10 FORMAT(4I7)
      END

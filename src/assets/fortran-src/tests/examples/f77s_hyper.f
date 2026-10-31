C     F77S REAL hyperbolic specifics and type-conversion rounding.
      PROGRAM HYPER
      REAL A,B,C,D,E,F,G,H
      INTRINSIC SINH,COSH,TANH,ANINT,ALOG
      A=SINH(0.5)
      B=COSH(0.5)
      C=TANH(0.5)
      D=ALOG(2.0)
      E=ANINT(-2.5)
      F=ANINT(2.5)
      G=REAL(3)
      H=TANH(-0.5)
      WRITE(6,10) A,B,C,D
   10 FORMAT(4F9.4)
      WRITE(6,20) E,F,G,H
   20 FORMAT(4F9.4)
      END

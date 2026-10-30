C     Local dummy scope, nested statement function, host variable preserved.
      PROGRAM STFUNC
      REAL T,F,G,A,B
      F(T)=T*T+A
      G(T)=F(T)+1.0
      A=2.0
      T=99.0
      B=G(3.0)
      WRITE(6,10) B,T
   10 FORMAT(2F9.2)
      END

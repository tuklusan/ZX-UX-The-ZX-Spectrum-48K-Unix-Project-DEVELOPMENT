      PROGRAM INTEST
      INTEGER N,M,K
      READ(5,10) N,M
   10 FORMAT(I4,1X,I3)
      K=N+M
      WRITE(6,20) K
   20 FORMAT(I4)
      END

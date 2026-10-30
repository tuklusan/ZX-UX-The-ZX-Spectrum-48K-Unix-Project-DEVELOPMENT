      PROGRAM DOTYPE
      INTEGER I,J,N,ST,T
      N=3
      ST=1
      T=0
      DO 10 I=1,N,ST
      T=T+I
   10 CONTINUE
      DO 20 J=3,1,-1
      T=T+J
   20 CONTINUE
      WRITE(6,30) T
   30 FORMAT(I5)
      END

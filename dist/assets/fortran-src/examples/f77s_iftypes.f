      PROGRAM IFTYPE
      INTEGER N,T
      LOGICAL L
      REAL R
      N=-3
      T=0
      IF(N) 10,20,30
   10 T=40
      GO TO 40
   20 T=2
      GO TO 40
   30 T=3
   40 R=0.0
      IF(R) 50,60,70
   50 T=T+9
      GO TO 80
   60 T=T+2
      GO TO 80
   70 T=T+10
   80 L=.TRUE.
      IF(L) T=T+1
      IF(.NOT.N.EQ.0) T=T+1
      WRITE(6,90) T
   90 FORMAT(I4)
      END

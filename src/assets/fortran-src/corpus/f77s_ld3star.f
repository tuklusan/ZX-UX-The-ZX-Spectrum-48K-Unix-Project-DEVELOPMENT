C     Rank-three dummy has adjustable leading and assumed-size tail.
      PROGRAM LDTHRE
      INTEGER A(2,2,2),N,X
      DATA A/1,2,3,4,5,6,7,8/
      N=2
      CALL ALTER(N,A,X)
      WRITE(6,10) X,A(1,2,2)
   10 FORMAT(2I5)
      END
      SUBROUTINE ALTER(N,B,X)
      INTEGER N,B(N,2,*),X
      X=B(2,2,2)
      B(1,2,2)=77
      END

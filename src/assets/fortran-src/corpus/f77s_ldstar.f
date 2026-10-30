C     Adjustable leading dimension plus assumed-size trailing bound.
      PROGRAM LDSTAR
      INTEGER A(2,3),N,X
      DATA A/1,2,3,4,5,6/
      N=2
      CALL CHANGE(N,A,X)
      WRITE(6,10) X,A(1,3)
   10 FORMAT(2I5)
      END
      SUBROUTINE CHANGE(N,B,X)
      INTEGER N,B(N,*),X
      X=B(2,3)
      B(1,3)=99
      END

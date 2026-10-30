C     Rank-2 DATA array in subprogram persists over two calls.
      PROGRAM SBARR
      INTEGER X
      X=0
      CALL DATARR(X)
      WRITE(6,10) X
      X=0
      CALL DATARR(X)
      WRITE(6,10) X
   10 FORMAT(I4)
      END
      SUBROUTINE DATARR(X)
      INTEGER X,A(2,2)
      DATA A/1,2,3,4/
      X=A(2,1)+A(2,2)
      RETURN
      END

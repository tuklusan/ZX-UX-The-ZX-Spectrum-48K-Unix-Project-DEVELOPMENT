C     INTEGER-only arithmetic subscript expression in F77S.
      PROGRAM IDXEXP
      INTEGER A(3),I,X
      DATA A/10,20,30/
      I=1
      X=A(I+1)
      WRITE(6,10) X
   10 FORMAT(I4)
      END

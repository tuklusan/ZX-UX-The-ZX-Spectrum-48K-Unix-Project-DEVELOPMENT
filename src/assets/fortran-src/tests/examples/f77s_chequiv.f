C     F77S same-length CHARACTER total EQUIVALENCE and array overlap.
      PROGRAM CHEQ
      CHARACTER*3 A(3),B(2),C
      EQUIVALENCE (A(2),B(1)),(A(3),C)
      A(1)='AA'
      A(2)='BB'
      A(3)='CC'
      WRITE(6,10) B(1),B(2),C,A(1)
   10 FORMAT(A3,1X,A3,1X,A3,1X,A3)
      END

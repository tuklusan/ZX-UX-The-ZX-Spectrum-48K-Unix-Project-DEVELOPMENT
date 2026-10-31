      PROGRAM EQUIV
      INTEGER A(4), B, C(2)
      EQUIVALENCE (A(3),B),(A(2),C(1))
      A(1)=10
      A(2)=11
      A(3)=12
      A(4)=13
      C(2)=42
      WRITE(6,10) B,A(3),C(1),C(2)
   10 FORMAT(4I4)
      END
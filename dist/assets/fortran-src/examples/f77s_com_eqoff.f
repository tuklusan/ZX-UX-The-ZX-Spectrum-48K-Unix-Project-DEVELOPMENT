C     Exact COMMON storage sequence with a nonzero local array offset.
      PROGRAM CMEQOF
      INTEGER A(4),B(3)
      COMMON /BLK/ A
      EQUIVALENCE (A(2),B(2))
      B(2)=42
      CALL SHOW()
      END
      SUBROUTINE SHOW()
      INTEGER C(4)
      COMMON /BLK/ C
      WRITE(6,10) C(1),C(2),C(3)
   10 FORMAT(3I4)
      END

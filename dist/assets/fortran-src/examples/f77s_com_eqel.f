C     A local scalar is storage-associated with an exact COMMON array element.
      PROGRAM CMEQ
      INTEGER A(3),B
      COMMON /BLK/ A
      EQUIVALENCE (A(2),B)
      B=42
      CALL SHOW()
      END
      SUBROUTINE SHOW()
      INTEGER C(3)
      COMMON /BLK/ C
      WRITE(6,10) C(2)
   10 FORMAT(I4)
      END

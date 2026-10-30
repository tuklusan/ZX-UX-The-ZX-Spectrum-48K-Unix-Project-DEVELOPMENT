      PROGRAM CMAR
      INTEGER A(2,3)
      COMMON /BLK/ A
      A(2,3)=42
      CALL INCR()
      WRITE(6,10) A(2,3)
   10 FORMAT(I4)
      END
      SUBROUTINE INCR()
      INTEGER B(6)
      COMMON /BLK/ B
      B(6)=B(6)+1
      RETURN
      END

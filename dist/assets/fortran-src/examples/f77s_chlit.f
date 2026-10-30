C     CHARACTER literal actual argument is a read-only dummy.
      PROGRAM CHLIT
      CALL SHOWN('HELLO')
      END
      SUBROUTINE SHOWN(S)
      CHARACTER*5 S
      WRITE(6,10) S
   10 FORMAT(A5)
      END

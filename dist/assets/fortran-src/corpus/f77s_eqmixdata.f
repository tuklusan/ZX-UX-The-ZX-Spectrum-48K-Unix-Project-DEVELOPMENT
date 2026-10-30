C     Mixed numeric EQUIVALENCE DATA initializes raw storage once.
      PROGRAM EQMD
      CALL GETV()
      CALL GETV()
      END
      SUBROUTINE GETV()
      INTEGER I
      REAL R
      EQUIVALENCE (I,R)
      DATA I/42/
      WRITE(6,10) I
   10 FORMAT(I4)
      END

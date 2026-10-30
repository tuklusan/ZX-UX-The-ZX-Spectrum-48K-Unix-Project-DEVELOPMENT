C     Static DATA initializes EQUIVALENCE storage once in a subprogram.
      PROGRAM EQDAT
      INTEGER FIRST,SECOND
      CALL TALLY(FIRST)
      CALL TALLY(SECOND)
      WRITE(6,10) FIRST,SECOND
   10 FORMAT(2I5)
      END
      SUBROUTINE TALLY(N)
      INTEGER A(2),B,N
      EQUIVALENCE (A(2),B)
      DATA A/40,41/
      N=B
      B=B+1
      END

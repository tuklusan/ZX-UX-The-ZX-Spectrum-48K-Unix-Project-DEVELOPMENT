C     Strict F77S constant-length CHARACTER dummy by-reference.
      PROGRAM CARGS
      CHARACTER*5 A
      DATA A/'ABC'/
      CALL CHPASS(A)
      WRITE(6,10) A
   10 FORMAT(A5)
      END
      SUBROUTINE CHPASS(C)
      CHARACTER*5 C
      CALL CHSET(C)
      RETURN
      END
      SUBROUTINE CHSET(C)
      CHARACTER*5 C
      C='HI'
      RETURN
      END

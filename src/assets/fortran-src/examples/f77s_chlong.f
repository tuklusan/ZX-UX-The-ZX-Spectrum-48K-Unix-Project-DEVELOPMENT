C     A longer CHARACTER actual binds to a shorter dummy by reference.
      PROGRAM CHLONG
      CHARACTER*5 A
      A='ABCDE'
      CALL SHRINK(A)
      WRITE(6,10) A
   10 FORMAT(A5)
      END
      SUBROUTINE SHRINK(C)
      CHARACTER*3 C
      C='XYZ'
      END

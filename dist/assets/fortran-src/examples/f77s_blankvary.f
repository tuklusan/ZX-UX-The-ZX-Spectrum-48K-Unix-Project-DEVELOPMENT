C     Blank COMMON can have different declared lengths in each unit.
      PROGRAM BLSZ
      INTEGER X,Y,Z
      COMMON X,Y,Z
      X=4
      Y=40
      Z=7
      CALL INC()
      CALL BUMP()
      WRITE(6,10) X,Y,Z
   10 FORMAT(3I4)
      END
      SUBROUTINE INC()
      INTEGER A,B
      COMMON A,B
      B=B+2
      END
      SUBROUTINE BUMP()
      INTEGER A
      COMMON A
      A=A+1
      END

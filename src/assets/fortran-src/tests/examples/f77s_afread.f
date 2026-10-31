C     Assigned FORMAT in formatted READ, numeric FORMAT for WRITE.
      PROGRAM AFRD
      INTEGER K,A,B
      ASSIGN 10 TO K
      READ(5,K) A,B
      WRITE(6,20) A,B
   10 FORMAT(2I4)
   20 FORMAT(2I5)
      END

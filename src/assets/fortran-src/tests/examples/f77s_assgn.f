C     Standard assigned label transfer, including a forward ASSIGN target.
      PROGRAM ASSGN
      INTEGER K,X
      ASSIGN 30 TO K
      GO TO K, (20,30)
   20 X=7
      GO TO 40
   30 X=42
   40 WRITE(6,10) X
   10 FORMAT(I4)
      END

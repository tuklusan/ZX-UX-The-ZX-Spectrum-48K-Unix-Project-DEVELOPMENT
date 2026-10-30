C     ASSIGNed FORMAT statement labels select numeric output width.
      PROGRAM AFMT
      INTEGER K,X
      X=42
      ASSIGN 10 TO K
      WRITE(6,K) X
      ASSIGN 20 TO K
      WRITE(6,K) X
   10 FORMAT(I4)
   20 FORMAT(I6)
      END

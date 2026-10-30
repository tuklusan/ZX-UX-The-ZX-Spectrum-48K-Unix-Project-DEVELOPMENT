      PROGRAM CHARR
      CHARACTER*(5) A
      READ(5,10) A
      WRITE(6,20) A
   10 FORMAT(A3)
   20 FORMAT('>',A5,'<')
      END

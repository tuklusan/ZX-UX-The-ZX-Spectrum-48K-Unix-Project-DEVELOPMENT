C     Sequential unformatted records each containing two INTEGER items.
      PROGRAM SEQP
      INTEGER A,B,C,D
      A=4
      B=5
      WRITE(7) A,B
      A=-42
      B=17
      WRITE(7) A,B
      BACKSPACE 7
      READ(7) C,D
      WRITE(6,10) C,D
   10 FORMAT(2I5)
      REWIND 7
      READ(7) C,D
      WRITE(6,10) C,D
      END

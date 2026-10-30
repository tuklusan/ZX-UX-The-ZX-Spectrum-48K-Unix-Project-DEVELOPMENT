C     Unnamed sequential unformatted INTEGER records and BACKSPACE.
      PROGRAM SEQI
      INTEGER A,B
      A=41
      WRITE(7) A
      A=-17
      WRITE(7) A
      BACKSPACE 7
      READ(7) B
      WRITE(6,10) B
   10 FORMAT(I5)
      REWIND 7
      READ(7) B
      WRITE(6,10) B
      END

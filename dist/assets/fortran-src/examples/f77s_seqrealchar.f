C     Mixed REAL/CHARACTER sequential unformatted records.
      PROGRAM SRC
      REAL A,B
      CHARACTER*4 C,D
      A=1.5
      C='AB'
      WRITE(7) A,C
      REWIND 7
      READ(7) B,D
      WRITE(6,10) B,D
   10 FORMAT(F5.1,A4)
      END

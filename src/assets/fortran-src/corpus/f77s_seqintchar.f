C     Mixed INTEGER and CHARACTER sequential unformatted record.
      PROGRAM SIC
      INTEGER A,B
      CHARACTER*4 C,D
      A=-42
      C='AB'
      WRITE(7) A,C
      REWIND 7
      READ(7) B,D
      WRITE(6,10) B,D
   10 FORMAT(I5,A4)
      END

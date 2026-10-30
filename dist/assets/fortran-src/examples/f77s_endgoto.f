C     Sequential unformatted END= branches at endfile record.
      PROGRAM EGO
      INTEGER A,B
      A=7
      WRITE(7) A
      ENDFILE 7
      REWIND 7
      READ(7) B
      READ(7,END=100) A
      A=99
  100 CONTINUE
      WRITE(6,10) B,A
   10 FORMAT(2I5)
      END

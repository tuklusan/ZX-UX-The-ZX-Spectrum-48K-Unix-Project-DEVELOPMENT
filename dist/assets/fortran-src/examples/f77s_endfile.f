C     ENDFILE writes a checked unnamed sequential endfile record.
      PROGRAM EFILE
      INTEGER A,B
      A=23
      WRITE(7) A
      ENDFILE 7
      REWIND 7
      READ(7) B
      WRITE(6,10) B
   10 FORMAT(I5)
      END

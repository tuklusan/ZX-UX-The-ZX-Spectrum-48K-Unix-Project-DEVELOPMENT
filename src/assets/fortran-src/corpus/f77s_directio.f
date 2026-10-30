C     Restricted unnamed direct-access unformatted INTEGER scratch records.
      PROGRAM DREC
      INTEGER A,B,REC
      OPEN(7,ACCESS='DIRECT',RECL=4)
      A=-42
      REC=2
      WRITE(7,REC=REC) A
      A=9
      WRITE(7,REC=1) A
      READ(7,REC=2) B
      WRITE(6,10) B
      READ(7,REC=1) B
      WRITE(6,10) B
   10 FORMAT(I5)
      END

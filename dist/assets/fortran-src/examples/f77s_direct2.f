C     Direct unformatted two INTEGER scalars per RECL=8 scratch record.
      PROGRAM DIR2
      INTEGER A,B,R
      OPEN(7,ACCESS='DIRECT',RECL=8)
      A=-42
      B=17
      WRITE(7,REC=2) A,B
      A=9
      B=-8
      R=1
      WRITE(7,REC=R) A,B
      READ(7,REC=2) A,B
      WRITE(6,10) A,B
   10 FORMAT(2I5)
      READ(7,REC=1) A,B
      WRITE(6,10) A,B
      END

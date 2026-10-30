C     Simple FORMAT reversion transfers 5 values across three records.
      PROGRAM REVERT
      INTEGER A(5),I
      READ(5,10) (A(I),I=1,5)
   10 FORMAT(2I3)
      WRITE(6,20) A
   20 FORMAT(2I4)
      END

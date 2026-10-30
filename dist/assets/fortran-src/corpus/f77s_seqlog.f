C     LOGICAL scalar sequential unformatted records with EOF status.
      PROGRAM SLOG
      LOGICAL A,B,C
      INTEGER S
      A=.TRUE.
      B=.FALSE.
      WRITE(7) A
      WRITE(7) B
      REWIND 7
      READ(7) C
      WRITE(6,10) C
   10 FORMAT(L3)
      READ(7,IOSTAT=S) C
      WRITE(6,20) C,S
   20 FORMAT(L3,I4)
      ENDFILE 7
      REWIND 7
      READ(7) C
      READ(7) C
      READ(7,END=100,IOSTAT=S) C
      STOP
  100 WRITE(6,30) S
   30 FORMAT(I4)
      END

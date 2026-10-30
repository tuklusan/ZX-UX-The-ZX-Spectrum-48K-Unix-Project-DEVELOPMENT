C     Mixed INTEGER/REAL unformatted records with END/IOSTAT handling.
      PROGRAM MIXEND
      INTEGER I,J,K
      REAL R,S
      I=-42
      R=1.25
      WRITE(7) I,R
      ENDFILE 7
      REWIND 7
      READ(7,IOSTAT=K,END=90) J,S
      WRITE(6,10) J,S,K
   10 FORMAT(I7,F9.2,I5)
      READ(7,END=90,IOSTAT=K) J,S
      STOP
   90 WRITE(6,20) K
   20 FORMAT(I5)
      END

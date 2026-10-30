C     Mixed INTEGER/CHARACTER unformatted END and IOSTAT controls.
      PROGRAM SICE
      INTEGER A,B,S
      CHARACTER*4 C,D
      A=-42
      C='AB'
      WRITE(7) A,C
      REWIND 7
      READ(7,IOSTAT=S) B,D
      WRITE(6,10) B,D,S
   10 FORMAT(I5,A4,I2)
      ENDFILE 7
      REWIND 7
      READ(7) B,D
      READ(7,END=100,IOSTAT=S) B,D
      STOP
  100 WRITE(6,20) S
   20 FORMAT(I4)
      END

C     REAL scalar 5-byte ZX ROM floating record, REWIND/BACKSPACE.
      PROGRAM SREAL
      REAL A,B,C
      INTEGER S
      A=1.25
      B=-3.5
      WRITE(7) A
      WRITE(7) B
      BACKSPACE 7
      READ(7) C
      WRITE(6,10) C
   10 FORMAT(F8.2)
      REWIND 7
      READ(7,IOSTAT=S) C
      WRITE(6,20) C,S
   20 FORMAT(F8.2,I5)
      ENDFILE 7
      REWIND 7
      READ(7) C
      READ(7,END=100,IOSTAT=S) C
      STOP
  100 WRITE(6,30) S
   30 FORMAT(I4)
      END

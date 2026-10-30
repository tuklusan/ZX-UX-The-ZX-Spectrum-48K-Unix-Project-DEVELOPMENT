C     Fixed CHARACTER sequential unformatted records and EOF.
      PROGRAM SCHAR
      CHARACTER*4 A,B,C
      INTEGER S
      A='AB'
      B='WXYZ'
      WRITE(7) A
      WRITE(7) B
      BACKSPACE 7
      READ(7) C
      WRITE(6,10) C
   10 FORMAT(A4)
      REWIND 7
      READ(7,IOSTAT=S) C
      WRITE(6,20) C,S
   20 FORMAT(A4,I4)
      ENDFILE 7
      REWIND 7
      READ(7) C
      READ(7,END=100,IOSTAT=S) C
      STOP
  100 WRITE(6,30) S
   30 FORMAT(I4)
      END

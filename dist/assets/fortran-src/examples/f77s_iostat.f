C     IOSTAT= and END= permitted control for unformatted scratch READ.
      PROGRAM IOST
      INTEGER A,B,S
      A=23
      WRITE(7) A
      ENDFILE 7
      REWIND 7
      READ(7,IOSTAT=S) B
      READ(7,IOSTAT=S,END=100) B
      B=99
  100 CONTINUE
      WRITE(6,10) B,S
   10 FORMAT(2I5)
      END

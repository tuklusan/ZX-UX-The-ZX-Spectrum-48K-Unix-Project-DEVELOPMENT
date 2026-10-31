C     Four INTEGER values in unformatted records and BACKSPACE.
      PROGRAM SQUAD
      INTEGER A,B,C,D,W,X,Y,Z,S
      A=-17
      B=42
      C=0
      D=32767
      WRITE(7) A,B,C,D
      WRITE(7) B,C,D,A
      BACKSPACE 7
      READ(7) W,X,Y,Z
      WRITE(6,10) W,X,Y,Z
   10 FORMAT(4I8)
      REWIND 7
      READ(7,IOSTAT=S) W,X,Y,Z
      WRITE(6,20) W,X,Y,Z,S
   20 FORMAT(5I8)
      ENDFILE 7
      REWIND 7
      READ(7) W,X,Y,Z
      READ(7,END=100,IOSTAT=S) W,X,Y,Z
      STOP
  100 WRITE(6,30) S
   30 FORMAT(I4)
      END

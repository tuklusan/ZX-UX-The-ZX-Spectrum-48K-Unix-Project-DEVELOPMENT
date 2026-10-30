C     Three INTEGERs in one unformatted sequential scratch record.
      PROGRAM STRI
      INTEGER A,B,C,X,Y,Z,S
      A=-42
      B=0
      C=32767
      WRITE(7) A,B,C
      ENDFILE 7
      REWIND 7
      READ(7,IOSTAT=S) X,Y,Z
      WRITE(6,10) X,Y,Z,S
   10 FORMAT(4I8)
      READ(7,END=100,IOSTAT=S) X,Y,Z
      STOP
  100 WRITE(6,20) S
   20 FORMAT(I4)
      END

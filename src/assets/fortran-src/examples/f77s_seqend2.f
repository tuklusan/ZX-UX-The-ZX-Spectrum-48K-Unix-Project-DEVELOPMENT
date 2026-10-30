C     Two-INTEGER sequential unformatted END and IOSTAT control.
      PROGRAM SEEN2
      INTEGER A,B,C,D,S
      A=-42
      B=17
      WRITE(7) A,B
      ENDFILE 7
      REWIND 7
      READ(7) C,D
      READ(7,IOSTAT=S,END=100) A,B
      C=99
  100 CONTINUE
      WRITE(6,10) C,D,S
   10 FORMAT(3I5)
      END

C     Checked twos complement INTEGER multiplication within range.
      PROGRAM IMUL
      INTEGER A,B,C,D,E
      A=-16384
      B=2
      C=-120
      D=A*B
      E=C*B
      WRITE(6,10) D,E
   10 FORMAT(2I8)
      END

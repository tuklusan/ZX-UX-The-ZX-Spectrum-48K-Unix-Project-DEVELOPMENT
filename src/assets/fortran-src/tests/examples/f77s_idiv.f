C     INTEGER division truncates toward zero and guards the signed edge.
      PROGRAM IDIV
      INTEGER A,B,C,D,E,F,G
      A=-32768
      B=2
      C=-17
      D=5
      E=A/B
      F=C/D
      G=D/(-2)
      WRITE(6,10) E,F,G
   10 FORMAT(3I8)
      END

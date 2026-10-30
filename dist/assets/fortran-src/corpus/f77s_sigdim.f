C     Specific numeric SIGN/ISIGN/DIM/IDIM and signed zero transfer.
      PROGRAM SDIM
      INTEGER A,B,C,D
      REAL E,F,G,H
      A=ISIGN(-7,2)
      B=ISIGN(7,-2)
      C=IDIM(12,5)
      D=IDIM(-4,5)
      E=SIGN(-2.5,1.0)
      F=SIGN(2.5,-1.0)
      G=DIM(6.5,1.5)
      H=DIM(-3.0,1.0)
      WRITE(6,10) A,B,C,D
   10 FORMAT(4I6)
      WRITE(6,20) E,F,G,H
   20 FORMAT(4F9.2)
      END

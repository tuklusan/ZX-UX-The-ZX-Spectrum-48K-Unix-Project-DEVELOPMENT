C     ANSI subset specific MIN/MAX and result-type conversion.
      PROGRAM MMAX
      INTEGER A,B,C,D
      REAL E,F,G,H
      A=MAX0(-4,7,3)
      B=MIN0(7,-4,3)
      C=MAX1(1.5,3.5,2.5)
      D=MIN1(1.5,3.5,-2.5)
      E=AMAX1(-1.5,3.25,2.5)
      F=AMIN1(-1.5,3.25,2.5)
      G=AMAX0(-4,7,3)
      H=AMIN0(-4,7,3)
      WRITE(6,10) A,B,C,D
   10 FORMAT(4I5)
      WRITE(6,20) E,F,G,H
   20 FORMAT(4F9.2)
      END

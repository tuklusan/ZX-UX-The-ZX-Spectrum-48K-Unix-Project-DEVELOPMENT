C     Signed INTEGER addition/subtraction at the 16-bit boundaries.
      PROGRAM IADSUB
      INTEGER A,B,C,D,E,F
      A=-32768
      B=1
      C=A+B
      D=32767
      E=D-B
      F=C-B
      WRITE(6,10) C,E,F
   10 FORMAT(3I8)
      END

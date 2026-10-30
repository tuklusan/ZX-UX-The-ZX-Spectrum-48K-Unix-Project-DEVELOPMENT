C     Signed 16-bit INTEGER powers, including biggest negative result.
      PROGRAM IPOW
      INTEGER A,B,C,D,E
      A=2**14
      B=(-2)**15
      C=1**32767
      D=0**0
      E=(-3)**3
      WRITE(6,10) A,B,C,D,E
   10 FORMAT(5I8)
      END

C     Mixed numeric exponent types and right-associative real powers.
      PROGRAM RPOW
      REAL R,A,B,C,D,E
      INTEGER I
      I=3
      R=2.0**I
      A=9.0**0.5
      B=2**2.0
      C=2.0**-2
      D=(-2.0)**3
      E=2.0**3**2
      WRITE(6,10) R,A,B,C,D,E
   10 FORMAT(6F9.2)
      END

C     Unformatted CHARACTER records support the full 1..255 F77S width.
      PROGRAM SC65
      CHARACTER*65 A,B
      A='HELLO'
      WRITE(7) A
      REWIND 7
      READ(7) B
      WRITE(6,10) B
   10 FORMAT(A5)
      END

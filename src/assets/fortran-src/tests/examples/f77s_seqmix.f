C     INTEGER and REAL in the same unnamed scratch unformatted record.
      PROGRAM SQMIX
      INTEGER I,J
      REAL R,S
      I=-42
      R=1.25
      WRITE(7) I,R
      REWIND 7
      READ(7) J,S
      WRITE(6,10) J,S
   10 FORMAT(I7,F9.2)
      END

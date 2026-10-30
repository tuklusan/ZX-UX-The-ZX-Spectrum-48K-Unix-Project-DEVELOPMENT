C     Standard PAUSE code and operator input on ZX-UX console.
      PROGRAM PAUSER
      INTEGER N
      N=42
      PAUSE 99
      WRITE(6,10) N
   10 FORMAT(I4)
      END

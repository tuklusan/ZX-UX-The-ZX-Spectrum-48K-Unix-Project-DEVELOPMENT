C     ANSI F77S Lw LOGICAL formatted READ/WRITE regression.
      PROGRAM LFORMT
      LOGICAL A(2)
      DATA A/.TRUE.,.FALSE./
      WRITE(6,10) A(1),A(2)
      READ(5,10) A(1),A(2)
      WRITE(6,10) A(1),A(2)
   10 FORMAT(2L4)
      END

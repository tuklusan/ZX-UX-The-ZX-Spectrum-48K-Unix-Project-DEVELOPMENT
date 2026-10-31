C     Implied-DO formatted READ and whole-array output.
      PROGRAM IORD
      INTEGER A(3),I
      READ(5,10) (A(I),I=1,3)
   10 FORMAT(3I3)
      WRITE(6,20) A,I
   20 FORMAT(4I4)
      END

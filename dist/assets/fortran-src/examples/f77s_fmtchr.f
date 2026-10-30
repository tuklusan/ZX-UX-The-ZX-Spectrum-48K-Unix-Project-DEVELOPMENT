C     CHARACTER literal FORMAT in both formatted READ and WRITE.
      PROGRAM FCHRD
      INTEGER A,B
      READ(5,'(2I4)') A,B
      WRITE(6,'(2I5)') A,B
      END

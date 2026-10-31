C     F77S fixed-length CHARACTER COMMON association across subprograms.
      PROGRAM CCHAR
      CHARACTER*4 S
      COMMON /TEXT/ S
      S='HI'
      CALL SHOW()
      END
      SUBROUTINE SHOW()
      CHARACTER*4 C
      COMMON /TEXT/ C
      WRITE(6,10) C
   10 FORMAT(A4)
      END

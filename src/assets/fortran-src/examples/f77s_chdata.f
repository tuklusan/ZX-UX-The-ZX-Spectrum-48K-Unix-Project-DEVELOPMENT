C     ANSI F77S CHARACTER DATA initialization and SAVE lifetime.
      PROGRAM CHDAT
      CHARACTER*5 A
      DATA A/'A/B'/
      WRITE(6,10) A
   10 FORMAT(A5)
      CALL SUB()
      CALL SUB()
      END
      SUBROUTINE SUB()
      CHARACTER*3 S
      DATA S/'AB'/
      WRITE(6,20) S
      S='XY'
   20 FORMAT(A3)
      RETURN
      END

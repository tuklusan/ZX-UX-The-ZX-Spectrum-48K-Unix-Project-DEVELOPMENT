C     Mixed-width CHARACTER COMMON uses packed storage and typed mirrors.
      PROGRAM CHMX
      CHARACTER*2 A(2)
      COMMON /TXT/ A
      A(1)='AB'
      A(2)='CD'
      CALL SHOW()
      WRITE(6,20) A(1),A(2)
   20 FORMAT(A2,1X,A2)
      END
      SUBROUTINE SHOW()
      CHARACTER*3 B
      COMMON /TXT/ B
      WRITE(6,10) B
   10 FORMAT(A3)
      B='XYZ'
      END

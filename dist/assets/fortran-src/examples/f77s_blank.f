      PROGRAM BLNK
      INTEGER N
      COMMON N
      N=40
      CALL AD2()
      WRITE(6,10) N
   10 FORMAT(I4)
      END
      SUBROUTINE AD2()
      INTEGER X
      COMMON // X
      X=X+2
      RETURN
      END
C     F77S CHARACTER array COMMON with exact matching storage.
      PROGRAM CHARR
      CHARACTER*3 S(2)
      COMMON /TXT/ S
      S(1)='AB'
      S(2)='CD'
      CALL SHOW()
      END
      SUBROUTINE SHOW()
      CHARACTER*3 C(2)
      COMMON /TXT/ C
      WRITE(6,10) C(1),C(2)
   10 FORMAT(A3,1X,A3)
      END

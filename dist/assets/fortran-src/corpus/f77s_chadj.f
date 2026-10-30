C     Adjustable CHARACTER dummy array with checked element capacity.
      PROGRAM CHADJ
      CHARACTER*3 A(5)
      A(1)='ONE'
      A(5)='FIV'
      CALL ALTER(5,A)
      WRITE(6,10) A(1),A(5)
   10 FORMAT(2A3)
      END
      SUBROUTINE ALTER(N,A)
      INTEGER N
      CHARACTER*3 A(N)
      A(N)='END'
      END

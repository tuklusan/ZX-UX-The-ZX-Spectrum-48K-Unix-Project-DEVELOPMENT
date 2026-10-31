C     F77S main unit, separately compiled with STEPER.
      PROGRAM SEPM
      INTEGER N,K
      COMMON /SHR/ K
      N=40
      K=0
      CALL STEPER(N)
      WRITE(6,10) N
   10 FORMAT(I4)
      END

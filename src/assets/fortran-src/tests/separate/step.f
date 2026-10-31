C     Independent F77S subroutine translation unit.
      SUBROUTINE STEPER(N)
      INTEGER N,K
      COMMON /SHR/ K
      N=N+2
      K=K+1
      END

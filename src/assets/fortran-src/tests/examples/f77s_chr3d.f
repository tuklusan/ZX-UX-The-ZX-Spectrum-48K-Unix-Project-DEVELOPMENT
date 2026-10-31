C     Rank-three CHARACTER column-major element association.
      PROGRAM CHR3D
      CHARACTER*2 A(2,2,2)
      INTEGER I,J,K
      DATA A/'AA','BB','CC','DD','EE','FF','GG','HH'/
      I=2
      J=1
      K=2
      A(I,J,K)='42'
      WRITE(6,10) A(2,1,2),A(1,2,2)
   10 FORMAT(2A2)
      END

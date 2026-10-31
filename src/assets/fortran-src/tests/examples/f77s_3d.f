      PROGRAM AR3D
      INTEGER C(2,2,2),S
      C(2,2,2)=7
      C(1,1,1)=4
      S=C(2,2,2)+C(1,1,1)
      WRITE(6,10) S
   10 FORMAT(I3)
      END

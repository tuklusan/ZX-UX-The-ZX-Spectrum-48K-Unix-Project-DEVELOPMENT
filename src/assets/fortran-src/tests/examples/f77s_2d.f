      PROGRAM AR2D
      INTEGER A(2,3),I,J,S
      DO 20 J=1,3
      DO 10 I=1,2
      A(I,J)=I+J*10
   10 CONTINUE
   20 CONTINUE
      S=A(1,1)+A(2,3)
      WRITE(6,30) S
   30 FORMAT(I4)
      END

C     DATA INITIALIZATION MUST FOLLOW ALL C48 LOCAL DECLARATIONS.
      PROGRAM DATADO
      INTEGER A(3),I,S,K
      DATA A/3,7,11/
      S=0
      DO 10 I=1,3
         S=S+A(I)
   10 CONTINUE
      K=1
      GO TO (20,30),K
   20 S=S+21
      GO TO 40
   30 S=0
   40 CONTINUE
      IF (S-42) 50,60,50
   50 S=0
   60 WRITE(6,100) S
  100 FORMAT(I4)
      END

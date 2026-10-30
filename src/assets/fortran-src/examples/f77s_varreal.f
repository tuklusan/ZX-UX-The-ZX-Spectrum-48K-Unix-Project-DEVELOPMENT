C     Runtime REAL implied-DO formatted input and reversed output.
      PROGRAM VRIO
      REAL A(4)
      INTEGER I,N
      N=4
      READ(5,10) (A(I),I=1,N)
   10 FORMAT(2F7.2)
      WRITE(6,20) (A(I),I=N,1,-1)
   20 FORMAT(2F9.2)
      WRITE(6,30) I
   30 FORMAT(I4)
      END

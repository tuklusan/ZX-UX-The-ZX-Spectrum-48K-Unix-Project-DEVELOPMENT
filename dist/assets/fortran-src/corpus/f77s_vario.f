C     Runtime-variable bounds and negative step in formatted I/O DO.
      PROGRAM VARD
      INTEGER A(5),I,N
      DATA A/1,2,3,4,5/
      N=5
      WRITE(6,10) (A(I),I=1,N)
   10 FORMAT(2I4)
      READ(5,20) (A(I),I=N,1,-1)
   20 FORMAT(2I3)
      WRITE(6,10) (A(I),I=1,N)
      WRITE(6,30) I
   30 FORMAT(I4)
      END

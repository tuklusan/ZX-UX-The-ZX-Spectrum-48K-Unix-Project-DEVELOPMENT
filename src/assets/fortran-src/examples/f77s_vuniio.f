C     Runtime I/O implied-DO using scalar INTEGER input/output units.
      PROGRAM VUNIO
      INTEGER A(5),I,N,INU,OUTU
      DATA A/1,2,3,4,5/
      N=5
      INU=5
      OUTU=6
      WRITE(OUTU,10) (A(I),I=1,N)
   10 FORMAT(2I4)
      READ(INU,20) (A(I),I=N,1,-1)
   20 FORMAT(2I3)
      WRITE(OUTU,10) (A(I),I=1,N)
      WRITE(OUTU,30) I
   30 FORMAT(I4)
      END

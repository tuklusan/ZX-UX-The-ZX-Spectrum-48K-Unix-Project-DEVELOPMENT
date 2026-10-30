C     Whole-array and literal-control implied DO in column-major order.
      PROGRAM IODO
      INTEGER A(3),I
      DATA A/2,4,6/
      WRITE(6,10) (A(I),I=1,3)
   10 FORMAT(3I4)
      WRITE(6,20) A
   20 FORMAT(3I4)
      WRITE(6,30) I
   30 FORMAT(I4)
      END

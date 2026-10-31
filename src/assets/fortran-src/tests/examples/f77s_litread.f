C     Runtime implied-DO formatted READ with literal controls.
      PROGRAM LITRD
      INTEGER A(3),I,N
      N=3
      READ(5,10) (A(I),I=1,N)
   10 FORMAT('>',I3,',',I3,',',I3)
      WRITE(6,20) A
   20 FORMAT(3I4)
      END

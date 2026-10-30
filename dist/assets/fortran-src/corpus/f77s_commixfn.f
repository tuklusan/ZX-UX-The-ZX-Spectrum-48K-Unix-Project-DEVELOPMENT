C     Mixed numeric COMMON synchronization around a function expression.
      PROGRAM CMFX
      INTEGER A
      REAL R
      COMMON /MIX/ A,R
      A=1
      R=2.0
      A=GETI()
      WRITE(6,10) A
   10 FORMAT(I4)
      END
      INTEGER FUNCTION GETI()
      INTEGER X,Y
      COMMON /MIX/ X,Y
      X=42
      GETI=X
      END

C     Direct-access unformatted INTEGER with variable unit and RECL.
      PROGRAM DVAR
      INTEGER A,B,R,U,RCL
      U=7
      RCL=4
      OPEN(U,ACCESS='DIRECT',RECL=RCL)
      A=-42
      R=2
      WRITE(U,REC=R) A
      A=9
      READ(U,REC=R) B
      WRITE(6,10) B
   10 FORMAT(I5)
      END

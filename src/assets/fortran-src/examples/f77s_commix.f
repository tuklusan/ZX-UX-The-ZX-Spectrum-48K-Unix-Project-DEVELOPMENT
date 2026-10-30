C     Mixed numeric COMMON uses target-compatible typed mirrors.
      PROGRAM CMIX
      INTEGER A
      REAL R
      COMMON /MIX/ A,R
      A=1
      R=2.0
      CALL SETI()
      WRITE(6,10) A
   10 FORMAT(I4)
      END
      SUBROUTINE SETI()
      INTEGER X,Y
      COMMON /MIX/ X,Y
      X=42
      END

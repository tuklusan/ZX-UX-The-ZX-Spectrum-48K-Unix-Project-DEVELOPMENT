C     Mixed numeric COMMON with alternate array/scalar views.
      PROGRAM CMXA
      INTEGER A(2)
      REAL R
      COMMON /MIX/ A,R
      A(1)=1
      A(2)=2
      R=3.0
      CALL SETI()
      WRITE(6,10) A(1),A(2)
   10 FORMAT(2I4)
      END
      SUBROUTINE SETI()
      INTEGER X
      REAL Y(2)
      COMMON /MIX/ X,Y
      X=42
      END

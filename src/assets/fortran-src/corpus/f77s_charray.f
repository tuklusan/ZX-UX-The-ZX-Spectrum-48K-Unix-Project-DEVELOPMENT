C     Strict F77S constant-length rank-2 CHARACTER array test.
      PROGRAM CHARRY
      CHARACTER*3 A(2,2)
      INTEGER I,J
      DATA A/'AB','C','XY','Q'/
      I=2
      J=2
      A(I,J)='OK'
      IF (A(I,J).NE.'OK') GO TO 30
      WRITE(6,10) A(1,1),A(2,1)
      WRITE(6,10) A(1,2),A(2,2)
   10 FORMAT(2A3)
      CALL CHSTAT()
      CALL CHSTAT()
      STOP
   30 WRITE(6,20) I
   20 FORMAT(I3)
      END
      SUBROUTINE CHSTAT()
      CHARACTER*2 T(2)
      DATA T/'AB','CD'/
      WRITE(6,40) T(1),T(2)
      T(2)='EF'
   40 FORMAT(2A2)
      RETURN
      END

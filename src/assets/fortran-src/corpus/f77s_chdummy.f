C     Strict F77S CHARACTER array dummy and element-tail alias.
      PROGRAM CHDM
      CHARACTER*3 A(4)
      INTEGER I
      DATA A/'AA','BB','CC','DD'/
      I=2
      CALL CHPASS(A(I))
      CALL CHSET(A(1))
      WRITE(6,10) A(2),A(3),A(4)
      WRITE(6,20) A(1)
   10 FORMAT(3A3)
   20 FORMAT(A3)
      END
      SUBROUTINE CHPASS(B)
      CHARACTER*3 B(3)
      CALL CHMOVE(B)
      RETURN
      END
      SUBROUTINE CHMOVE(B)
      CHARACTER*3 B(3)
      B(1)='XY'
      B(3)='HI'
      RETURN
      END
      SUBROUTINE CHSET(C)
      CHARACTER*3 C
      C='EE'
      RETURN
      END

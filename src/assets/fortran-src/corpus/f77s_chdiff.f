C     Differing CHARACTER array widths use FORTRAN storage-sequence bytes.
      PROGRAM CHDI
      CHARACTER*5 A(2)
      A(1)='ABCDE'
      A(2)='FGHIJ'
      CALL TAKE(A)
      WRITE(6,10) A(1),A(2)
   10 FORMAT(2A5)
      END
      SUBROUTINE TAKE(B)
      CHARACTER*3 B(3)
      B(1)='XYZ'
      B(2)='QRS'
      B(3)='TUV'
      END

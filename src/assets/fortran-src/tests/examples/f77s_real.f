      PROGRAM REALIT
      A=1.25
      IF (A .GT. 1.0) THEN
        I=2
      ELSE
        I=0
      ENDIF
      WRITE(6,10) I
   10 FORMAT(I3)
      END

      PROGRAM CHART
      CHARACTER*5 A,B
      A='HI'
      B=A
      IF (B .EQ. 'HI') THEN
      WRITE(6,10) B
      ELSE
      WRITE(6,20) B
      ENDIF
      B='ABCDE'
      WRITE(6,30) B
   10 FORMAT('>',A7,'<')
   20 FORMAT('BAD:',A5)
   30 FORMAT('>',A3,'<')
      END

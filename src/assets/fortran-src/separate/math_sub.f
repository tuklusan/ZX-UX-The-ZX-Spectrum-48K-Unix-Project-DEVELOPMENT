C     REAL math and FORMAT helpers in a separate linked SSO.
      SUBROUTINE MSUB(X)
      REAL X,Y
      Y=SQRT(X)
      WRITE(6,10) Y
   10 FORMAT(F8.2)
      END

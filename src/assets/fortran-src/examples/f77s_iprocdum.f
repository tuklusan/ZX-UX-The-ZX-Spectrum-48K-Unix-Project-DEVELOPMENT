C     INTEGER procedure dummy and actual pair, both typed and by reference.
      PROGRAM IPROC
      INTEGER X,Y,Z
      EXTERNAL SQRI,DBLI
      X=3
      CALL USEF(SQRI,X,Y)
      CALL USEF(DBLI,X,Z)
      WRITE(6,10) Y,Z
   10 FORMAT(2I6)
      END
      SUBROUTINE USEF(F,X,Y)
      INTEGER F,X,Y
      EXTERNAL F
      Y=F(X)
      END
      INTEGER FUNCTION SQRI(T)
      INTEGER T
      SQRI=T*T
      END
      INTEGER FUNCTION DBLI(T)
      INTEGER T
      DBLI=T+T
      END

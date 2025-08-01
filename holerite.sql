WITH FOL AS (SELECT VRS.NUMCAD, VRS.CODEVE, EVC.DESEVE, EVC.TIPEVE, 
        VRS.REFEVE,
        VRS.VALEVE AS VAL, 
        VRS.VALEVE * 
        CASE EVC.TIPEVE 
          WHEN 1 THEN 1 
          WHEN 2 THEN 1 
          WHEN 3 THEN -1 
          WHEN 4 THEN 0
          WHEN 5 THEN 0
          WHEN 6 THEN 0
        END AS VALEVE, CAL.TIPCAL, CAL.PERREF, 
        CASE WHEN NVL(INF.BASINS,0) > NVL(BIN.TETFAI,0) THEN BIN.TETFAI ELSE INF.BASINS END AS BASEINSS,
        NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) AS BASEIR,
        case when NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) <= 2428.8 then 0 
             when NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) > 2428.8 and NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) <= 2826.65 then 7.5
             when NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) > 2826.65 and NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) <= 3751.05 then 15
             when NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) > 3751.05 and NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) <= 4664.68 then 22.5
             when NVL(IRF.BASCAL,0) + NVL(IRF.DEDSIM,0) > 4664.68 then 27.5
        end as faixaIR,
        SAL.VALSAL, 
        CASE 
          WHEN CAL.TIPCAL in (11,32) THEN CTD.TOTREM 
        END AS TOTREM,
        INC.INCIRM, INC.INCFGD
   FROM VETORH.R046VER VRS 
   JOIN VETORH.R044CAL CAL 
     ON (CAL.CODCAL = VRS.CODCAL) AND (CAL.NUMEMP = VRS.NUMEMP)
   JOIN VETORH.R008EVC EVC 
     ON (EVC.CODTAB = VRS.TABEVE) AND (EVC.CODEVE = VRS.CODEVE)
   JOIN VETORH.R008INC INC
     ON (INC.CODTAB = EVC.CODTAB) AND (INC.CODEVE = EVC.CODEVE) 
    AND INC.CMPINC = (SELECT MAX(AX2.CMPINC) FROM VETORH.R008INC AX2 WHERE AX2.CODTAB=INC.CODTAB AND AX2.CODEVE=INC.CODEVE)
   JOIN VETORH.R026INF BIN 
     ON (BIN.PERREF = (SELECT MAX(AX.PERREF) FROM VETORH.R026INF AX WHERE AX.PERREF <= :PERREF_PARAM ) AND BIN.CODFAI = 4)
   LEFT JOIN VETORH.R046INF INF 
     ON (INF.NUMEMP = VRS.NUMEMP) AND (INF.NUMCAD = VRS.NUMCAD) AND (INF.CODCAL = VRS.CODCAL)
   LEFT JOIN VETORH.R046IRF IRF 
     ON (IRF.NUMEMP = VRS.NUMEMP) AND (IRF.NUMCAD = VRS.NUMCAD) AND (IRF.TIPCOL = VRS.TIPCOL) AND (IRF.CODCAL = VRS.CODCAL)
    AND (IRF.TIPIRF = CASE WHEN CAL.TIPCAL = 32 THEN 'D' ELSE 'N' END )
   LEFT JOIN (SELECT HSA.NUMEMP, HSA.NUMCAD, HSA.VALSAL FROM VETORH.R038HSA HSA
               WHERE HSA.DATALT = (SELECT MAX(AX.DATALT) FROM VETORH.R038HSA AX WHERE AX.NUMEMP = HSA.NUMEMP AND AX.NUMCAD = HSA.NUMCAD AND AX.DATALT <= :PERREF_PARAM)
                 AND HSA.SEQALT = (SELECT MAX(AX.SEQALT) FROM VETORH.R038HSA AX WHERE AX.NUMEMP = HSA.NUMEMP AND AX.NUMCAD = HSA.NUMCAD AND AX.DATALT = HSA.DATALT)
                  ) SAL   
     ON (SAL.NUMEMP = VRS.NUMEMP) AND (SAL.NUMCAD = VRS.NUMCAD)
   LEFT JOIN VETORH.R054CTD CTD 
     ON (CTD.NUMEMP  = VRS.NUMEMP) AND (CTD.NUMCAD = VRS.NUMCAD) AND (CTD.CMPCTD = CAL.PERREF) AND (CTD.TIPCOL = VRS.TIPCOL)
   
  WHERE CAL.PERREF = :PERREF_PARAM
    AND VRS.NUMEMP = 11
    AND CAL.TIPCAL in (11,91,31,32) -- (11=Folha, 91=Adiantamento, 31=Decimo terceiro adiantamento, 32=Decimo terceiro integral)
    AND VRS.NUMCAD = :NUMCAD_PARAM
    AND CAL.TIPCAL = :TIPCAL_PARAM
 )  


SELECT EMP.RAZSOC, FUN.DATADM, FUN.NUMCAD, FUN.NOMFUN AS NOME, FUN.NUMCPF, FOL.CODEVE, FOL.DESEVE, FOL.TIPEVE,
       FOL.REFEVE AS "REFERÊNCIA", FOL.VALEVE AS VLRREAL, FOL.VAL AS VLRIMP, FOL.TIPCAL, FOL.PERREF,
       FUN.CODAGE, FUN.CONBAN, FUN.DIGBAN, CCU.NOMCCU as LOCAL, CAR.TITCAR as CARGO,
       FOL.VALSAL "SALBASE",
       FOL.BASEINSS,
       CASE WHEN FOL.TIPCAL IN (31,32) 
           THEN (SELECT SUM(NVL(AX.VALEVE,0)) 
                   FROM FOL AX
                   WHERE AX.INCFGD <> 'N')
       ELSE
           case 
             when nvl(FOL.TOTREM,0) = 0 then FOL.BASEINSS 
             else FOL.TOTREM + nvl((SELECT SUM(NVL(AX.VAL,0)) FROM FOL AX WHERE AX.CODEVE = 220),0) 
           end
       END AS BASFGTS,
       --case when FOL.BASEIR = 0 then FOL.BASEINSS else FOL.BASEIR end AS BASEIR,
       (SELECT SUM(NVL(AX.VALEVE,0)) 
          FROM FOL AX
         WHERE AX.INCIRM <> 'N'
           AND EXISTS(SELECT 1 FROM VETORH.R008EVB EVB WHERE EVB.CODTAB = 941 AND EVB.CODEVE = AX.CODEVE AND EVB.EVEBAS IN (9001,9002,9061,40,1))) AS BASEIR,
       FOL.faixaIR, fol.INCFGD, (SELECT COUNT(*) FROM VETORH.R008EVB EVB WHERE EVB.CODTAB = 941 AND EVB.CODEVE = FOL.CODEVE AND EVB.EVEBAS IN (9001,9002,9061,40,1)) AS CONTA,
       FOL.BASEIR as BASIRAX
 FROM FOL
 
   JOIN VETORH.R034FUN FUN ON (FUN.NUMCAD = FOL.NUMCAD) AND (FUN.NUMEMP = 11)
                          AND (FUN.TIPCOL = 1) AND FUN.NUMCAD NOT IN (211,212)
   JOIN VETORH.R030FIL EMP ON ((EMP.CODFIL = EMP.NUMEMP) OR (EMP.NUMEMP = 4 AND EMP.CODFIL = 1) OR (EMP.NUMEMP = 10 AND EMP.CODFIL = 1)) 
                         AND (EMP.NUMEMP = FUN.NUMEMP)                       
   LEFT JOIN (SELECT HCC.NUMEMP, HCC.NUMCAD, HCC.CODCCU FROM VETORH.R038HCC HCC
              WHERE HCC.DATALT = (SELECT MAX(MX.DATALT) 
                                    FROM VETORH.R038HCC MX 
                                   WHERE MX.NUMEMP = HCC.NUMEMP 
                                     AND MX.NUMCAD = HCC.NUMCAD
                                     AND MX.TIPCOL = HCC.TIPCOL)
                AND HCC.TIPCOL = 1) HCU ON (HCU.NUMEMP = FUN.NUMEMP) AND (HCU.NUMCAD = FUN.NUMCAD)                       
   LEFT JOIN VETORH.R018CCU CCU ON (CCU.NUMEMP = FUN.NUMEMP AND CCU.CODCCU = HCU.CODCCU)       
   LEFT JOIN VETORH.R024CAR CAR ON (CAR.CODCAR = FUN.CODCAR)
 order by nomfun, CODEVE 
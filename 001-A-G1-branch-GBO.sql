-- relay: env=tier2-dev system=GBO out=01-evidence/A-G1-branch-TGT.csv
SELECT b.PK AS branch_pk, b.DESCRIPTION AS branch, b.FK_LOCALGROUP AS group_pk, g.DESCRIPTION AS branch_group
FROM   PGT_STC.T_PGT_BRANCH_S b
LEFT   JOIN PGT_STC.T_PGT_BRANCH_GROUP_S g ON g.PK = b.FK_LOCALGROUP
WHERE  b.PK = 20007.4

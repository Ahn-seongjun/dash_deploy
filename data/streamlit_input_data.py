import cx_Oracle
import pandas  as pd

cx_Oracle.init_oracle_client(lib_dir=r"C:\oracle\instantclient_21_3")
connect = cx_Oracle.connect("CARREGISTDB", "pass", "192.168.0.114:1521/CARREGDB")
cursor = connect.cursor()

df = pd.read_sql("""
                select case when MBER_REGIST_NO is NULL then '법인및사업자'
                when (N.VHRNO like '%허%' or N.VHRNO like '%하%' or N.VHRNO like '%호%') and N.PRPOS_SE_NM = '영업용' then '법인및사업자'
                else decode(substr(MBER_REGIST_NO,1,3),NULL,'법인및사업자','10대','20대','80대','70대','90대','70대',substr(MBER_REGIST_NO,1,3)) end as AGE
                ,CAR_BT
                ,CAR_MOEL_DT
                ,CL_HMMD_IMP_SE_NM
                ,EXTRACT_DE
                ,s.use_fuel_nm FUEL
                ,case when MBER_REGIST_NO is NULL then '법인및사업자'
                when (N.VHRNO like '%허%' or N.VHRNO like '%하%' or N.VHRNO like '%호%') and N.PRPOS_SE_NM = '영업용' then '법인및사업자'
                else decode(substr(MBER_REGIST_NO,5,2),NULL,'법인및사업자',substr(MBER_REGIST_NO,5,2)) end as "M/F"
                ,ORG_CAR_MAKER_KOR
                ,case when MBER_REGIST_NO is NULL then '법인및사업자'
                when (N.VHRNO like '%허%' or N.VHRNO like '%하%' or N.VHRNO like '%호%') and N.PRPOS_SE_NM = '영업용' then '법인및사업자' else '개인' end OWNER_GB
                ,PRPOS_SE_NM
                ,case when (N.VHRNO like '%허%' or N.VHRNO like '%하%' or N.VHRNO like '%호%') and N.PRPOS_SE_NM = '영업용'
                then '렌트'
                when N.VHCTY_ASORT_NM = '승용'
                and N.PRPOS_SE_NM = '영업용'
                then '여객(승용)_택시'
                when N.VHCTY_ASORT_NM = '승합'
                and N.PRPOS_SE_NM = '영업용'
                then '여객(승합)_콜밴'
                when N.VHCTY_ASORT_NM in ('특수','화물')
                and N.PRPOS_SE_NM = '영업용'
                then '운수(화물)'
                WHEN N.PRPOS_SE_NM = '관용' THEN '관용'
                else '자가용' end USE_GB 
                ,USE_STRNGHLD_ADRES_NM
                ,N.VHCTY_ASORT_NM
                ,LAT "경도"
                ,LON "경도"

        from
                CARREGISTDB.REQST_NEW_CAR_MARKET_INFO N
                ,CARREGISTDB.TEST_CAR_SPMNNO_DETAIL_INFO S
                ,REGION_LAT_LONG R

            where
                N.EXTRACT_DE like '2023%'
                and N.REQST_SE_NM in ('신조차 신규등록','수입차 신규등록')
                and N.SPMNNO = S.SPMNNO(+)
                AND N.USE_STRNGHLD_ADRES_NM = R.REGION(+)
                and S.ORG_CAR_NATION is not NULL
                and S.GUBUN in ('1','2')
                and to_date(EXTRACT_DE, 'YYYYMMDD') - case when YBL_MD is not null and length(YBL_MD) = 6 and (substr(YBL_MD, 5, 2) between '01' and '12') then to_date(YBL_MD||'01', 'YYYYMMDD') else to_date(to_number(PRYE||'0101'), 'YYYYMMDD') end <= 365*3
                AND SP_LEN != '14'
                AND CAR_BT NOT IN ('버스','트럭','특장','-')

                """, con=connect)
df.to_csv("2023년 누적 데이터.csv")


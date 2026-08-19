from dbutils.pooled_db import PooledDB, TooManyConnections
import oracledb
from django.conf import settings
import time

def _make_oracle_pool(user, pwd, host, db):
    cfg = settings.ORACLE_POOL_CONFIG    
    return PooledDB(
		creator=oracledb,
		maxconnections=cfg['maxconnections'],
		mincached=cfg['mincached'],
		maxcached=cfg['maxcached'],
		blocking=cfg['blocking'],
		ping=cfg['ping'],
		user=user,
		password=pwd,
		dsn=f"{host}/{db}",
    )

pool_oracle_case = _make_oracle_pool(
    settings.CASE_PLSQL_USER,
    settings.CASE_PLSQL_PWD,
    settings.CASE_PLSQL_HOST,
    settings.CASE_PLSQL_DB,
)

def get_pooled_connection(pool, timeout_seconds=8, retry_interval=0.2):
    """帶逾時的借連線包裝函數：最多等 timeout_seconds 秒，超過就放棄並報錯"""
    start = time.time()
    while True:
        try:
            return pool.connection()
        except TooManyConnections:
            if time.time() - start > timeout_seconds:
                raise TimeoutError(f"等待資料庫連線超過 {timeout_seconds} 秒，連線可能已滿或有連線卡住未歸還")
            time.sleep(retry_interval)
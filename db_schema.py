"""
db_schema.py

Lista tablas y campos (columnas) de una base de datos MySQL.
Guarda salida en db_schema.log
"""
import os
import sys

LOG = 'db_schema.log'
creds = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', '123456'),
}
dbname = os.environ.get('DB_NAME', 'pruebas02')

out = []

def log(s=''):
    print(s)
    out.append(str(s))

try:
    import mysql.connector
    from mysql.connector import errorcode
except Exception as e:
    log(f'ERROR: mysql connector missing: {e}')
    with open(LOG,'w',encoding='utf-8') as f:
        f.write('\n'.join(out))
    sys.exit(2)

log(f"Connecting to {creds['host']}:{creds['port']} as {creds['user']} to inspect DB '{dbname}'")
try:
    conn = mysql.connector.connect(host=creds['host'], port=creds['port'], user=creds['user'], password=creds['password'], database=dbname)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [r[0] for r in cursor.fetchall()]
    if not tables:
        log(f"No tables found in database {dbname}")
    for t in tables:
        log('')
        log(f"TABLE: {t}")
        cursor.execute(f"SHOW COLUMNS FROM `{t}`")
        rows = cursor.fetchall()
        # columns: Field, Type, Null, Key, Default, Extra
        for row in rows:
            field, coltype, nulls, key, default, extra = row
            log(f"  - {field} | {coltype} | Null={nulls} | Key={key} | Default={default} | Extra={extra}")
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    log('ERROR: ' + str(err))
    out.append('\n')
    import traceback
    out.append(traceback.format_exc())

with open(LOG,'w',encoding='utf-8') as f:
    f.write('\n'.join(out))

if any(line.startswith('ERROR') for line in out):
    sys.exit(3)
else:
    sys.exit(0)

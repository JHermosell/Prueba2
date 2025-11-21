"""
db_check.py

Comprueba conexión a MySQL y existencia de la base de datos especificada.
Escribe resultados en stdout y en db_check.log
"""
import sys
import os
import traceback

LOG = 'db_check.log'
creds = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', ''),
}
# Si no hay variables de entorno, usamos las credenciales proporcionadas por el usuario
if creds['user'] == 'root' and creds['password'] == '':
    # fallback to provided credentials if none in env
    creds['user'] = 'root'
    creds['password'] = 'AmxL3_Xx'

db_to_check = os.environ.get('DB_NAME', 'pruebas_02')

out_lines = []

def log(msg):
    print(msg)
    out_lines.append(msg)

try:
    import mysql.connector
    from mysql.connector import errorcode
except Exception as e:
    log(f"ERROR: mysql-connector not installed: {e}")
    with open(LOG, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out_lines))
    sys.exit(2)

log(f"Attempting connection to {creds['host']}:{creds['port']} as {creds['user']}")
try:
    conn = mysql.connector.connect(host=creds['host'], port=creds['port'], user=creds['user'], password=creds['password'])
    log('Connected to MySQL server OK')
    cursor = conn.cursor()
    cursor.execute('SHOW DATABASES')
    dbs = [row[0] for row in cursor.fetchall()]
    log('Databases on server: ' + ', '.join(dbs))
    if db_to_check in dbs:
        log(f"Database '{db_to_check}' exists.")
        # try to connect to that database
        try:
            conn_db = mysql.connector.connect(host=creds['host'], port=creds['port'], user=creds['user'], password=creds['password'], database=db_to_check)
            log(f"Successfully connected to database '{db_to_check}'.")
            cur2 = conn_db.cursor()
            cur2.execute("SHOW TABLES")
            tables = [r[0] for r in cur2.fetchall()]
            log(f"Tables in {db_to_check}: {tables if tables else '<<no tables>>'}")
            cur2.close()
            conn_db.close()
        except mysql.connector.Error as e:
            log(f"ERROR connecting to database '{db_to_check}': {e}")
    else:
        log(f"Database '{db_to_check}' NOT found on server.")
    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        log('ERROR: Access denied (check user/password)')
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        log('ERROR: Database does not exist')
    else:
        log('ERROR: ' + str(err))
    log('Full traceback:')
    out_lines.append(traceback.format_exc())
except Exception as e:
    log('Unexpected error: ' + str(e))
    out_lines.append(traceback.format_exc())

with open(LOG, 'w', encoding='utf-8') as f:
    f.write('\n'.join(out_lines))

if any('ERROR' in ln for ln in out_lines):
    sys.exit(3)
else:
    sys.exit(0)

"""
db_fill.py

Inserta 200 registros de ejemplo en la tabla `tbl001` de la BD indicada.
- `registro_01`: nombre (Nombre Apellido)
- `registro_02`: profesión (de una lista)
- `registro_03`: float aleatorio entre 1100 y 3800 con 2 decimales

Usa variables de entorno para las credenciales: DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
Genera un log en `db_fill.log`.
"""
import os
import sys
import random
import time

LOG = 'db_fill.log'

creds = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', '123456'),
}
DB = os.environ.get('DB_NAME', 'pruebas02')
NUM = int(os.environ.get('DB_FILL_COUNT', '200'))

out = []
def log(s=''):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {s}"
    print(line)
    out.append(line)

try:
    import mysql.connector
    from mysql.connector import errorcode
except Exception as e:
    log(f'ERROR: mysql connector missing: {e}')
    with open(LOG,'w',encoding='utf-8') as f:
        f.write('\n'.join(out))
    sys.exit(2)

first_names = [
    'Luis','Ana','Carlos','María','Jorge','Lucía','Pedro','Sofía','Miguel','Elena',
    'Raúl','Isabel','Fernando','Patricia','Diego','Carmen','Andrés','Laura','Sergio','Marta'
]
last_names = [
    'García','Martínez','López','Sánchez','Pérez','Gómez','Rodríguez','Fernández','Ruiz','Hernández'
]
profesiones = [
    'Ingeniero','Profesor','Médico','Abogado','Arquitecto','Programador','Diseñador','Contador','Electricista','Técnico'
]

# Generador simple de nombre
def gen_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"

def gen_prof():
    return random.choice(profesiones)

def gen_val():
    return round(random.uniform(1100.0, 3800.0), 2)

try:
    log(f"Conectando a {creds['host']}:{creds['port']} como {creds['user']} a DB '{DB}'")
    conn = mysql.connector.connect(host=creds['host'], port=creds['port'], user=creds['user'], password=creds['password'], database=DB)
    cursor = conn.cursor()
    # Verify table exists
    cursor.execute("SHOW TABLES LIKE 'tbl001'")
    if cursor.fetchone() is None:
        log("ERROR: tabla 'tbl001' no encontrada en la base de datos. Abortando.")
        cursor.close()
        conn.close()
        with open(LOG,'w',encoding='utf-8') as f:
            f.write('\n'.join(out))
        sys.exit(4)

    # Count before
    cursor.execute("SELECT COUNT(*) FROM tbl001")
    before = cursor.fetchone()[0]
    log(f"Registros antes: {before}")

    # Check if id_registro is AUTO_INCREMENT
    cursor.execute("SHOW COLUMNS FROM tbl001 LIKE 'id_registro'")
    col = cursor.fetchone()
    auto_inc = False
    if col:
        # Field, Type, Null, Key, Default, Extra
        extra = col[5] if len(col) > 5 else ''
        if extra and 'auto_increment' in extra.lower():
            auto_inc = True

    if auto_inc:
        # Prepare insert without id
        sql = "INSERT INTO tbl001 (registro_01, registro_02, registro_03) VALUES (%s, %s, %s)"
        data = [(gen_name(), gen_prof(), gen_val()) for _ in range(NUM)]
    else:
        # Need to supply id_registro manually
        cursor.execute("SELECT MAX(id_registro) FROM tbl001")
        mx = cursor.fetchone()[0]
        start_id = (mx or 0) + 1
        sql = "INSERT INTO tbl001 (id_registro, registro_01, registro_02, registro_03) VALUES (%s, %s, %s, %s)"
        data = []
        for i in range(NUM):
            data.append((start_id + i, gen_name(), gen_prof(), gen_val()))

    log(f"Insertando {NUM} registros en tbl001 (en batch). auto_increment={auto_inc}")
    try:
        cursor.executemany(sql, data)
        conn.commit()
    except mysql.connector.Error as e:
        log(f"ERROR during insert: {e}")
        conn.rollback()
        cursor.close()
        conn.close()
        with open(LOG,'w',encoding='utf-8') as f:
            f.write('\n'.join(out))
        sys.exit(5)

    cursor.execute("SELECT COUNT(*) FROM tbl001")
    after = cursor.fetchone()[0]
    added = after - before
    log(f"Registros después: {after} (añadidos: {added})")

    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    log('ERROR: ' + str(err))
    import traceback
    out.append(traceback.format_exc())
    sys.exit(3)

with open(LOG,'w',encoding='utf-8') as f:
    f.write('\n'.join(out))

sys.exit(0)

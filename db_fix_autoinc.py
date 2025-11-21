"""
db_fix_autoinc.py

Comprueba si `id_registro` es AUTO_INCREMENT en `tbl001`. Si no lo es y es seguro,
lo convierte a AUTO_INCREMENT (manteniendo el tipo actual) y se asegura de que sea PRIMARY KEY.
Después muestra por terminal todas las filas de `tbl001`.

Genera un log en `db_fix_autoinc.log`.
Usa variables de entorno: DB_HOST, DB_PORT, DB_USER, DB_PASS, DB_NAME
"""
import os
import sys
import time

LOG = 'db_fix_autoinc.log'
creds = {
    'host': os.environ.get('DB_HOST', '127.0.0.1'),
    'port': int(os.environ.get('DB_PORT', '3306')),
    'user': os.environ.get('DB_USER', 'root'),
    'password': os.environ.get('DB_PASS', '123456'),
}
DB = os.environ.get('DB_NAME', 'pruebas02')

out = []

def log(s=''):
    ts = time.strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{ts}] {s}"
    print(line)
    out.append(line)

try:
    import mysql.connector
except Exception as e:
    log(f'ERROR: mysql connector missing: {e}')
    with open(LOG,'w',encoding='utf-8') as f:
        f.write('\n'.join(out))
    sys.exit(2)

try:
    log(f"Conectando a {creds['host']}:{creds['port']} como {creds['user']} a DB '{DB}'")
    conn = mysql.connector.connect(host=creds['host'], port=creds['port'], user=creds['user'], password=creds['password'], database=DB)
    cursor = conn.cursor()

    # Check table exists
    cursor.execute("SHOW TABLES LIKE 'tbl001'")
    if cursor.fetchone() is None:
        log("ERROR: tabla 'tbl001' no encontrada. Abortando.")
        cursor.close()
        conn.close()
        with open(LOG,'w',encoding='utf-8') as f:
            f.write('\n'.join(out))
        sys.exit(4)

    # Show column
    cursor.execute("SHOW COLUMNS FROM tbl001 LIKE 'id_registro'")
    col = cursor.fetchone()
    if not col:
        log("ERROR: columna 'id_registro' no encontrada en 'tbl001'. Abortando.")
        cursor.close()
        conn.close()
        with open(LOG,'w',encoding='utf-8') as f:
            f.write('\n'.join(out))
        sys.exit(5)

    # col: Field, Type, Null, Key, Default, Extra
    field, coltype, nulls, key, default, extra = (col + (None,)*6)[:6]
    log(f"Columna encontrada: {field} | {coltype} | Null={nulls} | Key={key} | Default={default} | Extra={extra}")

    if extra and 'auto_increment' in (extra or '').lower():
        log('La columna ya es AUTO_INCREMENT. No se realizan cambios.')
    else:
        # Antes de alterar: asegurar que la columna es INT-like
        if not coltype.lower().startswith('int') and 'int' not in coltype.lower():
            log(f"WARN: tipo de columna inesperado ('{coltype}'). Intentaré modificarlo a INT para AUTO_INCREMENT.")
            newtype = 'INT'
        else:
            newtype = coltype

        # Si no es PRIMARY KEY debemos comprobar si agregar PK es seguro
        if key != 'PRI':
            log("La columna no es PRIMARY KEY. Se intentará añadir PRIMARY KEY sobre id_registro.")
            # Check if there is another primary key
            cursor.execute("SHOW INDEX FROM tbl001 WHERE Key_name='PRIMARY'")
            pk = cursor.fetchone()
            if pk:
                log("ERROR: ya existe otra PRIMARY KEY distinta. No puedo añadir AUTO_INCREMENT sin alterar la PK existente. Abortando.")
                cursor.close()
                conn.close()
                with open(LOG,'w',encoding='utf-8') as f:
                    f.write('\n'.join(out))
                sys.exit(6)
            else:
                add_pk = True
        else:
            add_pk = False

        # Perform ALTER TABLE to set AUTO_INCREMENT
        try:
            alter_sql = f"ALTER TABLE tbl001 MODIFY COLUMN id_registro {newtype} NOT NULL AUTO_INCREMENT"
            log(f"Ejecutando: {alter_sql}")
            cursor.execute(alter_sql)
            if add_pk:
                log("Añadiendo PRIMARY KEY sobre id_registro")
                cursor.execute("ALTER TABLE tbl001 ADD PRIMARY KEY (id_registro)")
            conn.commit()
            log('ALTER completado con éxito.')
        except mysql.connector.Error as e:
            log(f"ERROR al ejecutar ALTER: {e}")
            conn.rollback()
            cursor.close()
            conn.close()
            with open(LOG,'w',encoding='utf-8') as f:
                f.write('\n'.join(out))
            sys.exit(7)

        # Re-check column
        cursor.execute("SHOW COLUMNS FROM tbl001 LIKE 'id_registro'")
        col2 = cursor.fetchone()
        if col2:
            log(f"Después: {col2}")

    # Mostrar todas las filas
    log('Consultando todas las filas de tbl001:')
    cursor.execute("SELECT * FROM tbl001 ORDER BY id_registro")
    rows = cursor.fetchall()
    # Print header
    cursor.execute("SHOW COLUMNS FROM tbl001")
    cols = [r[0] for r in cursor.fetchall()]
    log(' | '.join(cols))
    for r in rows:
        log(' | '.join([str(x) if x is not None else 'NULL' for x in r]))

    cursor.close()
    conn.close()
except mysql.connector.Error as err:
    log('ERROR: ' + str(err))
    import traceback
    out.append(traceback.format_exc())
    with open(LOG,'w',encoding='utf-8') as f:
        f.write('\n'.join(out))
    sys.exit(3)

with open(LOG,'w',encoding='utf-8') as f:
    f.write('\n'.join(out))

sys.exit(0)

import pandas as pd
from db import get_db_connection

conn = get_db_connection()
query = "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Prestamos'"
df = pd.read_sql(query, conn)

print("--- COLUMNAS DE TU TABLA PRESTAMOS EN SMARTERASP ---")
print(df.to_string(index=False))
conn.close()
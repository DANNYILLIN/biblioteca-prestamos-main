import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
import joblib
from db import get_db_connection

print("1. Conectando a la base de datos...")
conn = get_db_connection()

# Descargamos los préstamos finalizados
query = """
    SELECT FechaPrestamo, FechaDevolucionEstimada, EstadoPrestamo 
    FROM Prestamos 
    WHERE EstadoPrestamo IN ('Devuelto', 'Retrasado')
"""
df = pd.read_sql(query, conn)
conn.close()

print("2. Preparando datos y añadiendo Escuelas y Tipos de Usuario...")
df['FechaPrestamo'] = pd.to_datetime(df['FechaPrestamo'])
df['FechaDevolucionEstimada'] = pd.to_datetime(df['FechaDevolucionEstimada'])

df['DiasSolicitados'] = (df['FechaDevolucionEstimada'] - df['FechaPrestamo']).dt.days
df['DiaSemana'] = df['FechaPrestamo'].dt.dayofweek
df['Mes'] = df['FechaPrestamo'].dt.month
df['EsMoroso'] = df['EstadoPrestamo'].apply(lambda x: 1 if x == 'Retrasado' else 0)

# Simular Tipo de Usuario para el entrenamiento (70% Alumnos, 20% Docentes, 10% Personal)
np.random.seed(42)
df['TipoUsuario'] = np.random.choice(['Alumno', 'Docente', 'Personal'], size=len(df), p=[0.7, 0.2, 0.1])

# Simular Escuela/Carrera solo para Alumnos (basado en tus datos)
escuelas = ['Agronomía', 'Ingeniería de Sistemas', 'Ingeniería de Minas', 'Enfermería', 'Odontología']
df['Escuela'] = np.where(
    df['TipoUsuario'] == 'Alumno',
    np.random.choice(escuelas, size=len(df)),
    'No Aplica' # Docentes y personal no tienen "Escuela"
)

# Convertir variables de texto a números (One-Hot Encoding) para que la IA los entienda
df_modelo = pd.get_dummies(df, columns=['TipoUsuario', 'Escuela'])

# Quitamos las columnas originales que ya no sirven para entrenar
X = df_modelo.drop(['FechaPrestamo', 'FechaDevolucionEstimada', 'EstadoPrestamo', 'EsMoroso'], axis=1)
y = df_modelo['EsMoroso']

# Guardar los nombres EXACTOS de las columnas para que Flask arme los datos igualitos después
columnas_entrenamiento = X.columns.tolist()
joblib.dump(columnas_entrenamiento, 'columnas_modelo.joblib')

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("3. Entrenando el modelo con Escuelas y Tipos de Usuario...")
modelo = RandomForestClassifier(n_estimators=100, random_state=42, max_depth=6)
modelo.fit(X_train, y_train)

precision = accuracy_score(y_test, modelo.predict(X_test))
print(f"4. ¡Listo! Precisión del modelo: {precision * 100:.2f}%")

joblib.dump(modelo, 'modelo_morosidad.joblib')
print("5. Archivos 'modelo_morosidad.joblib' y 'columnas_modelo.joblib' actualizados.")
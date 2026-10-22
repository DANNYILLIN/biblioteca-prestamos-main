import pandas as pd
from db import get_db_connection
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier
import warnings
warnings.filterwarnings('ignore') # Para ocultar advertencias innecesarias de consola

print("📡 Conectando a la base de datos SQL Server...")
conn = get_db_connection()

# 1. Extraer los datos reales cruzando Préstamos con los Usuarios
query = """
SELECT 
    P.FechaPrestamo, 
    P.FechaDevolucionEstimada as FechaEstimada, 
    P.EstadoPrestamo,
    COALESCE(A.Escuela, 'No Aplica') as Escuela,
    CASE 
        WHEN A.DNI IS NOT NULL THEN 'Alumno'
        WHEN D.DNI IS NOT NULL THEN 'Docente'
        ELSE 'Personal'
    END as TipoUsuario
FROM Prestamos P
LEFT JOIN Alumnos A ON P.UsuarioDNI = A.DNI
LEFT JOIN Docentes D ON P.UsuarioDNI = D.DNI
"""
df = pd.read_sql(query, conn)
conn.close()
print(f"✅ Se extrajeron {len(df)} préstamos históricos.")

# 2. Ingeniería de características (Preparar los datos igual que tu API)
df['FechaPrestamo'] = pd.to_datetime(df['FechaPrestamo'])
df['FechaEstimada'] = pd.to_datetime(df['FechaEstimada'])

df['DiasSolicitados'] = (df['FechaEstimada'] - df['FechaPrestamo']).dt.days
df['DiaSemana'] = df['FechaPrestamo'].dt.dayofweek
df['Mes'] = df['FechaPrestamo'].dt.month

# Definir la variable objetivo: 1 si está Retrasado (Moroso), 0 si es Devuelto/Activo
df['Moroso'] = df['EstadoPrestamo'].apply(lambda x: 1 if x == 'Retrasado' else 0)

# Filtrar columnas útiles y convertir textos a columnas numéricas (0 y 1)
df_modelo = df[['DiasSolicitados', 'DiaSemana', 'Mes', 'Escuela', 'TipoUsuario', 'Moroso']]
df_modelo = pd.get_dummies(df_modelo, columns=['Escuela', 'TipoUsuario'])

# 3. Separar datos de entrenamiento (80%) y prueba (20%)
X = df_modelo.drop('Moroso', axis=1)
y = df_modelo['Moroso']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 4. Inicializar los 5 modelos exigidos por el ingeniero
modelos = {
    "Regresión Logística": LogisticRegression(max_iter=1000),
    "K-Nearest Neighbors (KNN)": KNeighborsClassifier(),
    "Support Vector Machine (SVM)": SVC(),
    "Árbol de Decisión": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(random_state=42)
}

print("\n🚀 ENTRENANDO Y COMPARANDO 5 MODELOS...\n")

# 5. Entrenar, predecir y mostrar precisión
for nombre, modelo in modelos.items():
    modelo.fit(X_train, y_train)
    predicciones = modelo.predict(X_test)
    precision = accuracy_score(y_test, predicciones)
    print(f"🔸 {nombre}: Precisión del {round(precision * 100, 2)}%")

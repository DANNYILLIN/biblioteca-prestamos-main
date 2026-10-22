import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier

# 1. Carga tu dataset real (cambia el nombre por tu archivo)
df = pd.read_csv('modelo_morosidad.joblib')

# 2. Define tus variables (Ajusta 'Moroso' al nombre real de tu columna objetivo)
X = df.drop('Moroso', axis=1) 
y = df['Moroso']

# Divide los datos (80% entrenamiento, 20% prueba)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# 3. Inicializa los 5 modelos solicitados
modelos = {
    "Regresión Logística": LogisticRegression(max_iter=1000),
    "Support Vector Machine (SVM)": SVC(),
    "K-Nearest Neighbors (KNN)": KNeighborsClassifier(),
    "Árbol de Decisión": DecisionTreeClassifier(random_state=42),
    "Random Forest": RandomForestClassifier(random_state=42)
}

# 4. Entrena y compara
print("--- COMPARATIVA DE 5 MODELOS DE MACHINE LEARNING ---")
for nombre, modelo in modelos.items():
    modelo.fit(X_train, y_train)
    predicciones = modelo.predict(X_test)
    precision = accuracy_score(y_test, predicciones)
    print(f"{nombre}: Precisión del {round(precision * 100, 2)}%")
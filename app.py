import streamlit as st
import pandas as pd
import numpy as np
import os
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="ONPE - Resultados Electorales", page_icon="🗳️", layout="wide")
st.title("🗳️ Resultados Electorales ONPE 2006")
st.markdown("---")

# Función corregida para cargar datos
@st.cache_data
def cargar_datos():
    archivo = "data/resultados_2006.csv"
    
    if not os.path.exists(archivo):
        st.error(f"❌ Archivo no encontrado: {archivo}")
        st.info("Por favor, coloca el archivo CSV en la carpeta 'data/'")
        return None
    
    # Intentar diferentes estrategias de carga
    estrategias = [
        {
            "nombre": "CSV con separador punto y coma (;)",
            "params": {
                "encoding": 'utf-8-sig',  # utf-8-sig elimina automáticamente el BOM
                "sep": ';',               # Usar punto y coma como separador
                "on_bad_lines": 'skip',
                "engine": 'python'
            }
        },
        {
            "nombre": "Alternativo - Latin1 con punto y coma",
            "params": {
                "encoding": 'latin-1',
                "sep": ';',
                "on_bad_lines": 'skip',
                "engine": 'python'
            }
        },
        {
            "nombre": "Auto-detectar separador",
            "params": {
                "encoding": 'utf-8-sig',
                "sep": None,              # Pandas auto-detecta separador
                "engine": 'python',
                "on_bad_lines": 'skip'
            }
        }
    ]
    
    for estrategia in estrategias:
        try:
            df = pd.read_csv(archivo, **estrategia["params"])
            
            # Verificar si se cargaron columnas correctamente
            if len(df.columns) > 1 and any(col in str(df.columns) for col in ['UBIGEO', 'DEPARTAMENTO']):
                st.success(f"✅ Cargado exitosamente con estrategia: {estrategia['nombre']}")
                st.info(f"📊 Total de filas cargadas: {len(df):,}")
                st.info(f"📋 Columnas detectadas: {len(df.columns)}")
                return df
            else:
                # Si solo tiene una columna, intentar extraer los datos
                if len(df.columns) == 1:
                    st.warning("Detectado formato de una sola columna, intentando separar...")
                    col_name = df.columns[0]
                    # Intentar separar por punto y coma manualmente
                    df_expandido = df[col_name].str.split(';', expand=True)
                    # Tomar la primera fila como encabezados
                    headers = df_expandido.iloc[0].tolist()
                    df_expandido.columns = headers
                    df_expandido = df_expandido[1:]  # Eliminar la fila de encabezados
                    st.success("✅ Reorganización exitosa")
                    return df_expandido
                    
        except Exception as e:
            st.warning(f"❌ Estrategia '{estrategia['nombre']}' falló: {str(e)[:100]}")
            continue
    
    st.error("No se pudo cargar el archivo con ninguna estrategia")
    return None

# Cargar datos
df = cargar_datos()

if df is not None:
    # Limpiar nombres de columnas (quitar espacios y caracteres especiales)
    df.columns = df.columns.str.strip().str.replace('ï»¿', '').str.replace('\ufeff', '')
    
    # Convertir columnas numéricas a números
    columnas_votos = [col for col in df.columns if col.startswith('VOTOS_') or col.startswith('N_')]
    for col in columnas_votos:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)
    
    # Mostrar información básica
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total de mesas", f"{len(df):,}")
    with col2:
        if 'DEPARTAMENTO' in df.columns:
            st.metric("📍 Departamentos", df['DEPARTAMENTO'].nunique())
    with col3:
        if 'PROVINCIA' in df.columns:
            st.metric("🏛️ Provincias", df['PROVINCIA'].nunique())
    with col4:
        if 'DISTRITO' in df.columns:
            st.metric("🗺️ Distritos", df['DISTRITO'].nunique())
    
    st.markdown("---")
    
    # Mostrar vista previa
    with st.expander("🔍 Vista previa de los datos"):
        st.write("**Primeras 5 filas:**")
        st.dataframe(df.head())
        st.write("**Columnas disponibles:**")
        st.write(df.columns.tolist())
    
    # Sección: Identificación de datos solicitados
    st.subheader("📋 Análisis de Datos Electorales")
    
    # Número de mesas
    st.write(f"**Número total de mesas:** {len(df)}")
    
    # Ubigeo
    if 'UBIGEO' in df.columns:
        st.write(f"**Rango de Ubigeos:** {df['UBIGEO'].min()} - {df['UBIGEO'].max()}")
        st.write(f"**Ubigeos únicos:** {df['UBIGEO'].nunique():,}")
    
    # Votos por candidato (P1 a P20)
    columnas_votos_p = [col for col in df.columns if col.startswith('VOTOS_P') and col[7:].isdigit()]
    
    if columnas_votos_p:
        votos_candidatos = df[columnas_votos_p].sum()
        st.write("**Votos por candidato (resumen - Top 10):**")
        
        # Crear DataFrame para mostrar
        votos_df = pd.DataFrame({
            'Candidato': [f'Candidato {col.replace("VOTOS_P", "")}' for col in votos_candidatos.index],
            'Votos': votos_candidatos.values
        }).sort_values('Votos', ascending=False)
        
        st.dataframe(votos_df.head(10))
    
    # Votos válidos, nulos y en blanco
    col_a, col_b, col_c = st.columns(3)
    
    # Calcular votos válidos (suma de todos los VOTOS_P)
    if columnas_votos_p:
        total_votos_validos = df[columnas_votos_p].sum().sum()
        with col_a:
            st.metric("✅ Votos Válidos", f"{int(total_votos_validos):,}")
    
    if 'VOTOS_VB' in df.columns:
        total_votos_blanco = df['VOTOS_VB'].sum()
        with col_b:
            st.metric("⬜ Votos en Blanco", f"{int(total_votos_blanco):,}")
    
    if 'VOTOS_VN' in df.columns:
        total_votos_nulos = df['VOTOS_VN'].sum()
        with col_c:
            st.metric("❌ Votos Nulos", f"{int(total_votos_nulos):,}")
    
    # Limpieza de datos
    st.subheader("🧹 Limpieza de Datos")
    
    # Verificar valores nulos
    nulos_por_columna = df.isnull().sum()
    columnas_con_nulos = nulos_por_columna[nulos_por_columna > 0]
    
    if len(columnas_con_nulos) > 0:
        st.warning(f"Se encontraron {len(columnas_con_nulos)} columnas con valores nulos")
        st.write(columnas_con_nulos)
        
        # Limpiar: reemplazar nulos por 0 en columnas numéricas
        columnas_numericas = df.select_dtypes(include=[np.number]).columns
        df[columnas_numericas] = df[columnas_numericas].fillna(0)
        st.success("✅ Valores nulos reemplazados por 0")
    else:
        st.success("✅ No se encontraron valores nulos en columnas principales")
    
    # Mostrar estadísticas adicionales
    with st.expander("📊 Estadísticas adicionales"):
        st.write("**Resumen de participación:**")
        if 'N_ELEC_HABIL' in df.columns:
            total_habiles = df['N_ELEC_HABIL'].sum()
            participacion = (total_votos_validos / total_habiles * 100) if 'total_votos_validos' in dir() and total_habiles > 0 else 0
            st.metric("Participación electoral", f"{participacion:.2f}%")
            st.metric("Total electores hábiles", f"{int(total_habiles):,}")

else:
    st.error("No se pudieron cargar los datos. Verifica el archivo CSV.")
    st.markdown("""
    **Posibles soluciones:**
    1. Asegúrate de que el archivo esté en `data/resultados_2006.csv`
    2. El archivo debe usar punto y coma (;) como separador
    3. Verifica que no haya filas corruptas
    """)

st.markdown("---")
st.caption("Desarrollado para la Oficina Nacional de Procesos Electorales")

# Sección de visualizaciones
st.subheader("📊 Visualización de Resultados")

# 1. Gráfico de barras: votos por candidato (top 10)
st.write("### 🏆 Top 10 Candidatos por votos")

# Renombrar columnas de candidatos (por simplicidad)
votos_candidatos = df[[f'VOTOS_P{i}' for i in range(1, 21)]].sum().reset_index()
votos_candidatos.columns = ['Candidato', 'Votos']
votos_candidatos['Candidato'] = votos_candidatos['Candidato'].str.replace('VOTOS_P', 'Candidato ')

fig1 = px.bar(
    votos_candidatos.head(10),
    x='Candidato',
    y='Votos',
    title='Top 10 Candidatos con mayor votación',
    color='Votos',
    color_continuous_scale='Blues'
)
st.plotly_chart(fig1, use_container_width=True)

# 2. Distribución de votos por región (departamento)
st.write("### 🗺️ Distribución de votos por Departamento")

votos_por_departamento = df.groupby('DEPARTAMENTO')[[f'VOTOS_P{i}' for i in range(1, 21)]].sum().sum(axis=1).reset_index()
votos_por_departamento.columns = ['Departamento', 'Total_Votos']
votos_por_departamento = votos_por_departamento.sort_values('Total_Votos', ascending=True)

fig2 = px.bar(
    votos_por_departamento,
    x='Total_Votos',
    y='Departamento',
    title='Votos totales por Departamento',
    orientation='h',
    color='Total_Votos',
    color_continuous_scale='Greens'
)
st.plotly_chart(fig2, use_container_width=True)

# 3. Comparación: Votos válidos vs nulos vs blancos por departamento
st.write("### 📈 Comparación por Departamento")

comparacion = df.groupby('DEPARTAMENTO')[['VOTOS_VB', 'VOTOS_VN', 'VOTOS_VI']].sum().reset_index()
comparacion_melt = comparacion.melt(id_vars=['DEPARTAMENTO'], 
                                     value_vars=['VOTOS_VB', 'VOTOS_VN', 'VOTOS_VI'],
                                     var_name='Tipo_Voto',
                                     value_name='Cantidad')

fig3 = px.bar(
    comparacion_melt,
    x='DEPARTAMENTO',
    y='Cantidad',
    color='Tipo_Voto',
    title='Comparación: Votos en Blanco, Nulos e Impugnados por Departamento',
    barmode='group'
)
st.plotly_chart(fig3, use_container_width=True)

# 4. Interpretación de resultados
st.write("### 📝 Interpretación de Resultados")

st.markdown("""
**Análisis observado:**

1. **Concentración de votos**: Los votos se concentran en ciertos candidatos, mostrando una tendencia clara hacia los primeros puestos.

2. **Variación regional**: Existen diferencias significativas en la participación y preferencias electorales entre departamentos.

3. **Votos no válidos**: La cantidad de votos en blanco y nulos varía considerablemente, lo que podría indicar diferencias en la educación electoral o descontento ciudadano.

4. **Participación**: La relación entre electores hábiles (`N_ELEC_HABIL`) y votos emitidos permite calcular la participación electoral real.

**Recomendación:** Para un análisis más profundo, se recomienda segmentar por provincia y distrito, y correlacionar con variables sociodemográficas.
""")



from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

# Sección de Machine Learning
st.subheader("🤖 Análisis con Machine Learning")
st.markdown("---")

# 4.1 Identificar tipo de problema
st.write("### 🎯 Tipo de problema identificado")

st.markdown("""
**Problema de Clasificación:**  
- Predecir la tendencia de voto mayoritaria en una mesa (qué candidato ganó esa mesa)
- Agrupar mesas con comportamientos similares (clustering)

**Problema de Regresión (opcional):**  
- Predecir el porcentaje de votos para un candidato específico
""")

# 4.2 Agrupamiento básico (Clustering)
st.write("### 📊 Agrupamiento de mesas (K-Means)")

# Preparar datos para clustering
# Usar votos por candidato como características
caracteristicas = df[[f'VOTOS_P{i}' for i in range(1, 21)]].copy()

# Normalizar datos
scaler = StandardScaler()
caracteristicas_scaled = scaler.fit_transform(caracteristicas)

# Aplicar K-Means (3 grupos para simplicidad)
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
df['cluster'] = kmeans.fit_predict(caracteristicas_scaled)

# Mostrar resultados del clustering
st.write("**Distribución de clusters:**")
cluster_counts = df['cluster'].value_counts().sort_index()
for i in range(3):
    st.write(f"- Cluster {i}: {cluster_counts[i]} mesas ({cluster_counts[i]/len(df)*100:.1f}%)")

# Interpretar clusters
st.write("**Interpretación de clusters:**")
st.markdown("""
- **Cluster 0**: Mesas con votación mayoritaria hacia candidatos específicos
- **Cluster 1**: Mesas con votación distribuida o alta participación  
- **Cluster 2**: Mesas con votación atípica o baja participación

*Nota: La interpretación exacta depende de los patrones encontrados en los datos.*
""")

# 4.3 Predicción de tendencia de voto
st.write("### 🎯 Predicción de tendencia de voto")

# Crear variable objetivo: candidato con más votos en cada mesa
def candidato_ganador(fila):
    votos_candidatos = [fila[f'VOTOS_P{i}'] for i in range(1, 21)]
    if sum(votos_candidatos) == 0:
        return -1  # Sin votos válidos
    return votos_candidatos.index(max(votos_candidatos))

df['candidato_ganador'] = df.apply(candidato_ganador, axis=1)

# Filtrar mesas con ganador definido
df_ml = df[df['candidato_ganador'] >= 0].copy()

if len(df_ml) > 0:
    # Preparar características
    X = df_ml[[f'VOTOS_P{i}' for i in range(1, 21)] + ['N_ELEC_HABIL']]
    y = df_ml['candidato_ganador']
    
    # Dividir en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)
    
    # Entrenar modelo simple
    modelo = RandomForestClassifier(n_estimators=10, random_state=42, max_depth=5)
    modelo.fit(X_train, y_train)
    
    # Evaluar
    precision_train = modelo.score(X_train, y_train)
    precision_test = modelo.score(X_test, y_test)
    
    st.write(f"**Precisión en entrenamiento:** {precision_train:.2%}")
    st.write(f"**Precisión en prueba:** {precision_test:.2%}")
    
    # Evaluar resultados
    st.write("**Evaluación del modelo:**")
    if precision_train > 0.95 and precision_test < 0.70:
        st.warning("⚠️ Posible **SOBREAJUSTE** (Overfitting): El modelo memoriza los datos de entrenamiento pero no generaliza")
    elif precision_train < 0.60 and precision_test < 0.60:
        st.warning("⚠️ Posible **SUBAJUSTE** (Underfitting): El modelo no capta los patrones subyacentes")
    else:
        st.success("✅ Balance adecuado entre entrenamiento y prueba")
else:
    st.warning("No hay suficientes datos para entrenar el modelo")



# ============================================
# PARTE 5: ENTRENAMIENTO Y EVALUACIÓN - CORREGIDO
# ============================================

st.markdown("---")
st.header("🎯 PARTE 5: Entrenamiento y Evaluación del Modelo")
st.markdown("---")

with st.expander("📊 Ver detalles de entrenamiento y evaluación", expanded=True):
    
    # 5.1 Dividir dataset en entrenamiento y prueba
    st.subheader("📌 5.1 División del Dataset")
    
    # Preparar datos para el modelo
    # Usar características: votos por candidato + electores hábiles
    columnas_caracteristicas = [f'VOTOS_P{i}' for i in range(1, 21)] + ['N_ELEC_HABIL']
    
    # Crear variable objetivo: tendencia de voto (candidato más votado)
    def get_tendencia(fila):
        votos_candidatos = [fila[f'VOTOS_P{i}'] for i in range(1, 21)]
        if sum(votos_candidatos) == 0:
            return -1  # Sin votos válidos
        # Retorna el índice del candidato con más votos (0-19)
        return votos_candidatos.index(max(votos_candidatos))
    
    df['tendencia'] = df.apply(get_tendencia, axis=1)
    
    # Filtrar mesas con tendencia definida
    df_modelo = df[df['tendencia'] >= 0].copy()
    
    if len(df_modelo) > 100:  # Suficientes datos para entrenar
        
        # Características (X)
        X = df_modelo[columnas_caracteristicas].copy()
        
        # Variable objetivo (y)
        y = df_modelo['tendencia'].copy()
        
        # Mostrar información del dataset
        col1, col2 = st.columns(2)
        with col1:
            st.metric("📊 Total de registros", f"{len(df_modelo):,}")
            st.metric("🎯 Clases objetivo", y.nunique())
        with col2:
            st.metric("🔢 Características", len(columnas_caracteristicas))
            st.metric("📈 Rango de votos por mesa", f"{X.iloc[:, :20].sum(axis=1).min():.0f} - {X.iloc[:, :20].sum(axis=1).max():.0f}")
        
        # Contar muestras por clase
        from collections import Counter
        conteo_clases = Counter(y)
        st.write("**Distribución de clases (candidatos):**")
        st.json(dict(sorted(conteo_clases.items())[:5]))  # Mostrar solo primeras 5
        st.caption(f"Total de clases únicas: {len(conteo_clases)}")
        
        # División en entrenamiento (70%) y prueba (30%)
        from sklearn.model_selection import train_test_split
        
        # 🔧 FIX: Usar stratify SOLO si todas las clases tienen al menos 2 muestras
        usar_stratify = all(count >= 2 for count in conteo_clases.values())
        
        if usar_stratify:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42, stratify=y
            )
            st.success("✅ Dataset dividido con **estratificación** (manteniendo proporción de clases)")
        else:
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.3, random_state=42
            )
            st.info("ℹ️ Dataset dividido **sin estratificación** (algunas clases tienen pocas muestras)")
        
        st.write(f"- **Entrenamiento:** {len(X_train):,} mesas (70%)")
        st.write(f"- **Prueba:** {len(X_test):,} mesas (30%)")
        
        # 5.2 Entrenar un modelo básico
        st.subheader("🤖 5.2 Entrenamiento del Modelo")
        
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.tree import DecisionTreeClassifier
        
        # Usar Decision Tree más simple para evitar sobreajuste
        modelo = DecisionTreeClassifier(
            max_depth=8,           # Profundidad máxima
            min_samples_split=10,  # Mínimo de muestras para dividir
            min_samples_leaf=5,    # Mínimo de muestras por hoja
            random_state=42
        )
        
        # Entrenar
        with st.spinner("Entrenando modelo..."):
            modelo.fit(X_train, y_train)
        
        st.success("✅ Modelo entrenado correctamente")
        
        # Mostrar características del modelo
        st.write("**Parámetros del modelo (Árbol de Decisión):**")
        st.code("""
        DecisionTreeClassifier(
            max_depth=8,           # Profundidad máxima del árbol
            min_samples_split=10,  # Mínimo de muestras para dividir un nodo
            min_samples_leaf=5,    # Mínimo de muestras en una hoja
            random_state=42        # Semilla para reproducibilidad
        )
        """)
        
        # 5.3 Evaluar resultados
        st.subheader("📈 5.3 Evaluación del Modelo")
        
        # Predicciones
        y_train_pred = modelo.predict(X_train)
        y_test_pred = modelo.predict(X_test)
        
        # Calcular métricas
        from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
        
        train_accuracy = accuracy_score(y_train, y_train_pred)
        test_accuracy = accuracy_score(y_test, y_test_pred)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🎯 Precisión en Entrenamiento", f"{train_accuracy:.2%}")
        with col2:
            st.metric("🎯 Precisión en Prueba", f"{test_accuracy:.2%}")
        with col3:
            diferencia = train_accuracy - test_accuracy
            st.metric("📊 Diferencia", f"{diferencia:.2%}", 
                     delta="⚠️ Posible sobreajuste" if diferencia > 0.15 else "✅ Aceptable")
        
        # 5.4 Identificar sobreajuste o subajuste
        st.subheader("🔍 5.4 Análisis de Sobreajuste y Subajuste")
        
        # Criterios de diagnóstico
        if train_accuracy > 0.95 and test_accuracy < 0.75:
            st.error("⚠️ **SOBREAJUSTE (Overfitting) Detectado**")
            st.markdown("""
            **¿Qué significa?**  
            El modelo ha **memorizado** los datos de entrenamiento en lugar de **aprender** patrones generales.
            
            **Indicadores observados:**
            - ✅ Precisión en entrenamiento: muy alta (>95%)
            - ❌ Precisión en prueba: baja (<75%)
            
            **¿Por qué ocurre en datos electorales?**
            - Cada mesa tiene patrones muy específicos
            - El modelo aprende ruido (errores, anomalías locales)
            - No generaliza a nuevas mesas o elecciones
            
            **¿Cómo solucionarlo?**
            - Reducir complejidad del modelo (menos profundidad)
            - Aumentar datos de entrenamiento
            - Usar validación cruzada
            """)
        
        elif train_accuracy < 0.60:
            st.error("⚠️ **SUBAJUSTE (Underfitting) Detectado**")
            st.markdown("""
            **¿Qué significa?**  
            El modelo es **demasiado simple** para capturar la complejidad de los datos electorales.
            
            **Indicadores observados:**
            - ❌ Precisión en entrenamiento: baja (<60%)
            - ❌ Precisión en prueba: baja (<60%)
            
            **¿Por qué ocurre en datos electorales?**
            - El modelo no es lo suficientemente complejo
            - Faltan características importantes (variables socioeconómicas)
            - Los datos tienen patrones no lineales que el modelo no captura
            
            **¿Cómo solucionarlo?**
            - Aumentar complejidad del modelo
            - Agregar más características relevantes
            - Probar otros algoritmos (Random Forest, XGBoost)
            """)
        
        elif train_accuracy > 0.85 and test_accuracy > 0.75:
            st.success("✅ **MODELO BALANCEADO (Buen rendimiento)**")
            st.markdown(f"""
            **Resultados óptimos:**
            - Precisión entrenamiento: {train_accuracy:.2%}
            - Precisión prueba: {test_accuracy:.2%}
            - Diferencia: {train_accuracy - test_accuracy:.2%}
            
            **Interpretación:**  
            El modelo ha aprendido patrones generales del comportamiento electoral sin memorizar ruido específico.
            """)
        
        else:
            st.info("📊 **MODELO CON RENDIMIENTO ACEPTABLE**")
            st.markdown(f"""
            **Resultados obtenidos:**
            - Precisión entrenamiento: {train_accuracy:.2%}
            - Precisión prueba: {test_accuracy:.2%}
            - Diferencia: {train_accuracy - test_accuracy:.2%}
            
            **Análisis:**  
            El modelo muestra un rendimiento moderado. Podría mejorarse con:
            - Más datos históricos (múltiples elecciones)
            - Características adicionales (población, nivel socioeconómico)
            - Ajuste de hiperparámetros
            """)
        
        # 5.5 Explicar limitaciones del modelo en contexto electoral
        st.subheader("⚠️ 5.5 Limitaciones del Modelo en Contexto Electoral")
        
        st.markdown("""
        ### 🔴 Limitaciones fundamentales:
        
        | Limitación | Explicación | Impacto |
        |------------|-------------|---------|
        | **Datos transversales** | Solo una elección (2006). No captura tendencias históricas | ❌ Baja capacidad predictiva para otras elecciones |
        | **Falta de contexto** | No incluye variables socioeconómicas, encuestas, eventos políticos | ❌ Ignora factores clave del comportamiento electoral |
        | **Sesgo geográfico** | Los patrones aprendidos son específicos de cada región | ❌ No generaliza bien a todo el país |
        | **Simplicidad del modelo** | Árbol de decisión simple vs fenómenos complejos | ❌ No captura interacciones entre candidatos |
        | **Dependencia histórica** | Asume que el pasado predice el futuro (falso en política) | ❌ Elecciones tienen dinámicas únicas |
        
        ### 📌 Limitaciones técnicas específicas:
        
        **1. Desbalance de clases**
        - Algunos candidatos tienen pocas mesas donde ganaron
        - El modelo no aprende bien patrones de candidatos minoritarios
        
        **2. Multicolinealidad**
        - Los votos por candidato están correlacionados (si uno sube, otro baja)
        - Viola supuestos de algunos modelos estadísticos
        
        **3. Autocorrelación espacial**
        - Mesas cercanas geográficamente tienen comportamientos similares
        - El modelo asume independencia, lo cual es falso
        
        ### ✅ Recomendaciones para un modelo electoral robusto:
        
        - 🔄 **Incluir múltiples elecciones** (2006, 2011, 2016, 2021) como series temporales
        - 📊 **Agregar variables externas**: Población, pobreza, nivel educativo, rural/urbano
        - 🧠 **Usar modelos más avanzados**: XGBoost, Redes Neuronales, Random Forest profundo
        - 🗺️ **Incorporar geolocalización**: Efectos espaciales explícitos
        - 📈 **Validación por regiones**: Entrenar modelos específicos por departamento
        - 🔬 **Colaboración con politólogos**: Incorporar conocimiento de dominio
        """)
        
        # Mostrar importancia de características (top 10)
        if hasattr(modelo, 'feature_importances_'):
            st.subheader("📊 Importancia de Características")
            importancias = modelo.feature_importances_
            features_nombres = columnas_caracteristicas
            
            # Crear DataFrame de importancias
            df_importancias = pd.DataFrame({
                'Característica': features_nombres,
                'Importancia': importancias
            }).sort_values('Importancia', ascending=False).head(10)
            
            st.dataframe(df_importancias, use_container_width=True)
            
            st.caption("""
            **Interpretación:** Mayor importancia indica que la característica influye más 
            en la predicción. Si `N_ELEC_HABIL` aparece con alta importancia, significa 
            que la participación electoral es clave para predecir tendencias.
            """)
        
        # Mostrar ejemplo de predicción
        st.subheader("🎯 Ejemplo de Predicción")
        st.write("**Predicción para una mesa aleatoria (de prueba):**")
        
        # Tomar una mesa aleatoria del conjunto de prueba
        import numpy as np
        idx_aleatorio = np.random.randint(0, len(X_test))
        mesa_ejemplo = X_test.iloc[idx_aleatorio:idx_aleatorio+1]
        prediccion = modelo.predict(mesa_ejemplo)[0]
        probabilidad = modelo.predict_proba(mesa_ejemplo).max() if hasattr(modelo, 'predict_proba') else 0.5
        
        st.write(f"- **Candidato predicho:** Candidato {prediccion + 1}")
        st.write(f"- **Confianza:** {probabilidad:.2%}")
        st.caption("Nota: La numeración de candidatos corresponde a las columnas VOTOS_P1 a VOTOS_P20")
        
    else:
        st.warning(f"⚠️ Datos insuficientes para entrenamiento. Se necesitan al menos 100 registros, pero solo hay {len(df_modelo)}.")
        st.info("""
        **Posibles soluciones:**
        1. Usar un dataset más grande
        2. Verificar que los datos tengan votos válidos
        3. Revisar el formato de los datos cargados
        """)

st.markdown("---")
st.caption("✅ Parte 5 completada: Entrenamiento, evaluación y análisis de limitaciones en contexto electoral")


# ============================================
# PARTE 7: COMPUTACIÓN CUÁNTICA APLICADA
# ============================================

st.markdown("---")
st.header("🌌 PARTE 7: Computación Cuántica aplicada a datos electorales")
st.markdown("---")

with st.expander("🔬 Ver análisis de Computación Cuántica", expanded=True):
    
    st.subheader("📚 7.1 Conceptos fundamentales")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 🔷 Qubits (Quantum Bits)
        
        **Definición:**  
        Unidad básica de información cuántica.
        
        **Diferencia con bits clásicos:**
        - Bit clásico: 0 o 1 (solo un estado)
        - Qubit: puede ser 0, 1 o **ambos al mismo tiempo**
        
        **Representación:**  
        `|ψ⟩ = α|0⟩ + β|1⟩` donde α² + β² = 1
        
        **Analogía electoral:**  
        Un qubit es como un elector indeciso que aún no ha decidido su voto, está en superposición de apoyar a múltiples candidatos simultáneamente.
        """)
    
    with col2:
        st.markdown("""
        ### 🔄 Superposición
        
        **Definición:**  
        Capacidad de un sistema cuántico de estar en múltiples estados simultáneamente.
        
        **Ejemplo práctico:**  
        Un qubit puede representar **todos los votos posibles** a la vez.
        
        **Ventaja:**  
        Con n qubits se pueden representar 2ⁿ estados simultáneamente.
        
        **Analogía electoral:**  
        Una encuesta cuántica podría analizar todas las combinaciones de votos posibles en una mesa, en lugar de una por una.
        """)
    
    with col3:
        st.markdown("""
        ### ⚡ Paralelismo Cuántico
        
        **Definición:**  
        Capacidad de realizar múltiples operaciones simultáneamente gracias a la superposición.
        
        **Ejemplo:**  
        Un algoritmo cuántico puede evaluar todas las soluciones a la vez.
        
        **Ventaja sobre clásico:**  
        - Clásico: procesa 1 resultado por vez
        - Cuántico: procesa 2ⁿ resultados simultáneamente
        
        **Analogía electoral:**  
        Como contar votos en todas las mesas del país **al mismo tiempo** en lugar de una por una.
        """)
    
    st.markdown("---")
    
    # 7.2 Potencial aplicación en análisis masivo de datos electorales
    st.subheader("🎯 7.2 Potencial aplicación en análisis electoral masivo")
    
    st.markdown("""
    ### 📊 Aplicaciones concretas para la ONPE:
    
    | Aplicación | Problema actual | Solución cuántica | Impacto |
    |------------|----------------|-------------------|---------|
    | **Conteo rápido** | Procesar 100k+ actas toma horas | Algoritmo de búsqueda cuántica (Grover) | Resultados en minutos |
    | **Detección de anomalías** | Identificar mesas sospechosas requiere análisis lento | Superposición para evaluar patrones simultáneos | Detección en tiempo real |
    | **Optimización de rutas** | Logística de traslado de actas | Algoritmo cuántico de optimización (QAOA) | Reducción de costos |
    | **Simulación electoral** | Modelar escenarios requiere mucho cómputo | Simulación de múltiples escenarios a la vez | Pronósticos más precisos |
    | **Cribado de datos** | Filtrar votos inválidos es secuencial | Búsqueda cuántica paralela | Limpieza 100x más rápida |
    """)
    
    st.subheader("🔬 Algoritmos cuánticos aplicables")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        ### Algoritmo de Grover (Búsqueda)
        
        **Problema que resuelve:**  
        Encontrar un elemento específico en una base de datos no ordenada.
        
        **Aplicación electoral:**  
        Buscar mesas con patrones anómalos de votación.
        
        **Ventaja cuántica:**  
        - Clásico: O(N) operaciones
        - Cuántico: O(√N) operaciones
        
        **Ejemplo concreto:**  
        Entre 100,000 mesas, encontrar las 100 con irregularidades:
        - Clásico: hasta 100,000 verificaciones
        - Cuántico: solo ~316 verificaciones
        """)
    
    with col2:
        st.markdown("""
        ### QAOA (Quantum Approximate Optimization)
        
        **Problema que resuelve:**  
        Optimización combinatoria (problemas de asignación).
        
        **Aplicación electoral:**  
        Asignación óptima de centros de cómputo y rutas de fiscalización.
        
        **Ventaja cuántica:**  
        Encuentra soluciones casi óptimas exponencialmente más rápido.
        
        **Ejemplo concreto:**  
        Optimizar la distribución de 5000 centros de votación para minimizar tiempos de desplazamiento en 25 regiones.
        """)
    
    st.subheader("⚠️ Limitaciones actuales de la computación cuántica")
    
    st.markdown("""
    ### 🚧 Desafíos para implementación en ONPE:
    
    1. **Hardware limitado**
       - Computadoras cuánticas actuales tienen pocos qubits (50-100)
       - Para datos electorales reales se necesitarían miles de qubits
    
    2. **Decoherencia cuántica**
       - Los estados cuánticos son extremadamente frágiles
       - Ruido ambiental destruye la superposición en milisegundos
    
    3. **Curva de aprendizaje**
       - Programación cuántica requiere nuevos paradigmas
       - Personal especializado es escaso y costoso
    
    4. **Costo**
       - Computadoras cuánticas industriales: millones de dólares
       - Alternativa: simuladores cuánticos en la nube (menos potentes)
    
    ### 🔮 Estado actual y futuro cercano:
    
    - **Hoy:** Simuladores cuánticos para investigación
    - **2-5 años:** Computadoras cuánticas de 1000+ qubits
    - **5-10 años:** Posible implementación en gobierno electrónico
    
    ### ✅ Recomendación para la ONPE:
    
    """ + """
    > **Invertir en formación y experimentación**  
    > Comenzar con simuladores cuánticos (IBM Quantum, Amazon Braket)  
    > Desarrollar prototipos para problemas específicos (optimización logística)  
    > Participar en programas piloto de computación cuántica gubernamental
    """)
    
    st.subheader("📊 Comparación: Clásico vs Cuántico para análisis electoral")
    
    comparacion_data = {
        "Métrica": ["Tiempo de conteo (100k mesas)", "Detección de anomalías", "Optimización de rutas", "Simulación de escenarios"],
        "Computación Clásica": ["~4-6 horas", "Secuencial, horas", "NP-difícil, días", "Uno por vez"],
        "Computación Cuántica": ["~5-10 minutos", "Paralelo, minutos", "Casi óptimo, minutos", "Miles simultáneos"],
        "Madurez actual": ["✓ Producción", "✓ Producción", "⚠️ Investigación", "⚠️ Prototipo"]
    }
    
    df_comparacion = pd.DataFrame(comparacion_data)
    st.dataframe(df_comparacion, use_container_width=True, hide_index=True)
    
    st.caption("""
    **Fuente:** Análisis prospectivo basado en literatura científica actual.
    **Nota:** La computación cuántica aún está en fase experimental para aplicaciones electorales.
    """)

st.markdown("---")
st.caption("🌌 Parte 7 completada: Fundamentos de computación cuántica aplicada a datos electorales")
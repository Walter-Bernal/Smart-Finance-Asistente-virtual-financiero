import streamlit as st
import google.generativeai as genai
import sqlite3
import pandas as pd
import os

st.set_page_config(page_title="Smart Finance", page_icon="💰")
st.title("🤖 Smart Finance")

# --- CONFIGURACIÓN ---
with st.sidebar:
    st.header("Estado")
    # 1. API Key
    try:
        if "general" in st.secrets:
            api_key = st.secrets["general"]["GOOGLE_API_KEY"]
            st.success("✅ API Key: OK")
            genai.configure(api_key=api_key)
        else:
            st.error("❌ Falta API Key en secrets")
            st.stop()
    except:
        st.error("❌ Error leyendo secretos")
        st.stop()


    # 2. Base de Datos
    DB_PATH = "CFO_SAP_PYL.db"
    if os.path.exists(DB_PATH):
        st.success("✅ DB: Cargada")
    else:
        st.warning("⚠️ Falta DB")
        up = st.file_uploader("Sube el archivo .db", type=["db"])
        if up:
            with open(DB_PATH, "wb") as f: f.write(up.getbuffer())
            st.rerun()


    # 3. AUTO-SELECCIÓN DE MODELO
    st.divider()
    try:
        # Buscamos qué modelos tienes habilitados
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # Preferencia: Flash > Pro > cualquiera
        valid_model = next((m for m in available_models if 'flash' in m), None)
        if not valid_model:
            valid_model = next((m for m in available_models if 'pro' in m), available_models[0])

        st.success(f"🧠 Modelo activo: {valid_model}")
    except Exception as e:
        st.error(f"Error buscando modelos: {e}")
        valid_model = None

# --- LÓGICA ---
def get_response(prompt, model_name):
    model = genai.GenerativeModel(model_name)

    # Paso 1: Intentar generar SQL
    sql_prompt = f'''
    Eres un Analista de Datos Financieros Senior experto en SQL (SQLite).
    Tu objetivo es traducir preguntas de negocio complejas a consultas SQL precisas sobre la tabla 'CFO_SAP_PYL'.


    ### 1. ESTRUCTURA DE DATOS Y VALORES
    * **IMPORTE**: Valor numérico (Float).
    * **ANIO**: Entero (Ej: 2023, 2024).
    * **MES_ID**: Entero formato YYYYMM (Ej: 202401, 202412).
    * **DICCIONARIO_Q**: Trimestres ('Q1', 'Q2', 'Q3', 'Q4').
    * **PYL0** (Conceptos): 'NET REVENUES', 'COGS', 'EXPENSES', 'TAX'.
    * **DICCIONARIO_COUNTRY**: 'ARGENTINA', 'BRASIL', 'CHILE', 'COLOMBIA', 'ECUADOR', 'PANAMA', 'PARAGUAY', 'PERU', 'URUGUAY', 'VENEZUELA'.
    * **MONEDA**: 'USD', 'LOCAL', 'DEFLATED', 'USD CC'.
    * **ESCENARIO**: 'REALIZADO', 'PLAN'.
    * **DICCIONARIO_SUBBU**: 'RETAIL', 'ONLINE PAYMENTS', 'CREDITS', 'POINT'.
    * **DICCIONARIO_MACRO_BU**: 'FINTECH SERVICES', 'E-COMMERCE'.

    ### 2. REGLAS DE LÓGICA DE NEGOCIO (OBLIGATORIAS)

    A. **NORMALIZACIÓN DE TEXTO:** - Los países en la BD están en MAYÚSCULAS. Siempre usa `UPPER(DICCIONARIO_COUNTRY) = 'ARGENTINA'` (o el país solicitado).
       - Corrige errores tipográficos obvios (Ej: "Ciolombia" -> 'COLOMBIA', "Tac" -> 'TAX').

    B. **DEFINICIONES FINANCIERAS:**
       - **"Ventas", "Ingresos", "Revenues"**: Filtra `PYL0 = 'NET REVENUES'`.
       - **"EBIT"**: No existe como campo. Debes calcularlo:
         `SUM(CASE WHEN PYL0 = 'NET REVENUES' THEN IMPORTE ELSE 0 END) - SUM(CASE WHEN PYL0 IN ('COGS', 'EXPENSES') THEN IMPORTE ELSE 0 END)`
        IMPORTANTE: NO uses la columna 'DICCIONARIO_LOCAL_EBIT' para este cálculo. IGNÓRALA.
       - **"Plan" vs "Real"**: Si piden "Plan", usa `ESCENARIO = 'PLAN'`. Si no especifican o dicen "Realizado", usa `ESCENARIO = 'REALIZADO'`.
       - **"MACRO BU" o "unidad de negocio**: Filtra o agrupas usando el campo DICCIONARIO_MACRO_BU
       - **"SUBBU" o "Sub unidad de negocios**: Filtras o agrupas usando el campo DICCIONARIO_SUBBU
       - **"PLAN" o "planificado"**: Filtra `ESCENARIO = 'PLAN'`.
       - **"REALIZADO" o "realizado"**: Filtra `ESCENARIO = 'REALIZADO'`.

    C. **MANEJO DE TIEMPO:**
       - **"Mayo 2024"**: `MES_ID = 202405`.
       - **"Q2 2024"**: `ANIO = 2024 AND DICCIONARIO_Q = 'Q2'`.
       - **"YTD a Octubre 2023"**: `ANIO = 2023 AND MES_ID <= 202310`.
       - **"YoY" (Year over Year)** o **"Variación"**: Debes seleccionar los datos de ambos periodos para poder comparar.
         *Ejemplo:* Si piden "Variación Q3 2024 vs Q2 2024", filtra `ANIO = 2024 AND DICCIONARIO_Q IN ('Q2', 'Q3')` y AGRUPA por `DICCIONARIO_Q`.

    D. **MONEDAS Y UNIDADES:**
       - **"LC" / "Moneda Local"**: `MONEDA = 'LOCAL'`.
       - **"USD"**: `MONEDA = 'USD'`.
       - **"Deflated"**: `MONEDA = 'DEFLATED'`.
       - Siempre que des un valor dalo por defecto USD salvo que se te pida de forma explicita otra cosa

    ### 3. INSTRUCCIONES TÉCNICAS SQL
    - Usa siempre `SUM(IMPORTE)` para métricas agregadas.
    - Si la pregunta implica comparar grupos (ej: "por país", "por trimestre"), SIEMPRE agrega `GROUP BY` y pon la columna de agrupación en el `SELECT`.
    - **SALIDA:** Solo el código SQL. Nada más.

    - **ESTRATEGIA PARA "VS" O "CRECIMIENTO":** Si preguntan "A vs B" o "Crecimiento", NO intentes calcular el porcentaje en SQL. Simplemente selecciona la columna de periodo (ej: DICCIONARIO_Q) y el importe, filtrando por ambos periodos.


    Pregunta: {prompt}
    '''
    try:
            resp = model.generate_content(sql_prompt)
            sql = resp.text.replace("```sql", "").replace("```", "").strip()

            # Verificar si parece SQL
            if not sql.upper().startswith("SELECT"):
                return "No pude generar una consulta SQL válida. Solo puedo dar información de Trade Alliance Corporation y se encuentren la base de datos", None

            # Ejecutar
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(sql, conn)
            conn.close()

            if df.empty:
                return "La consulta es válida pero no hay datos (verifica filtros).", sql

            # Explicar
            exp_prompt = f"Responde como Analista financiero de forma DIRECTA y BREVE (máximo 3 líneas). No des introducciones o saludos. Solo el dato exacto, el contexto mínimo y conclusiones muy concretas. Explica en español:\\nPregunta: {prompt}\\nDatos: {df.to_string()}"



            # Guardamos respuesta y retornamos AMBOS (explicación y sql)
            explanation = model.generate_content(exp_prompt).text
            return explanation, sql

    except Exception as e:
            # Retornamos tuple en caso de error también
            return f"Error técnico: {str(e)}", None

# --- CHAT ---
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Hola! Soy tu asistente financiero 'Smart Finance'. Soy un asistente cognitvo, una IA que puede dar explicaciones simples para contadores. No necesitas saber SQL, ni saber programar ni conocer sobre bases de datos. Yo me encargaré por ti y te dare la información que necesitas de una forma clara, sin tantas vueltas y explicada en lenguaje natural. ¿Qué consulta tienes?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

prompt = st.chat_input("Consulta...")

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    if not valid_model:
        st.error("No hay modelo disponible.")
    elif not os.path.exists(DB_PATH):
        st.error("Sube la base de datos.")
    else:
        with st.chat_message("assistant"):
            with st.spinner("Procesando..."):
                # Recibimos texto Y código sql
                response_text, sql_code = get_response(prompt, valid_model)

                # Mostramos la explicación
                st.markdown(response_text)

                # Si hay SQL, mostramos la cajita desplegable
                if sql_code:
                    with st.expander("🔎 Ver Query SQL Generado"):
                        st.code(sql_code, language="sql")

                # Guardamos en el historial
                st.session_state.messages.append({"role": "assistant", "content": response_text})

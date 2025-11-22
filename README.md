# 🤖 Smart Finance: Asistente Virtual Financiero

**Smart Finance** es una aplicación de inteligencia artificial diseñada para democratizar el acceso a datos financieros. Actúa como un analista cognitivo que permite a contadores y gerentes consultar métricas complejas de negocio utilizando lenguaje natural, sin necesidad de conocimientos en SQL, programación o bases de datos.

## 🚀 Funcionalidades Principales

* **Interacción en Lenguaje Natural:** Pregunta como si hablaras con un colega (ej: *"¿Cuál fue el EBIT de Argentina en Q1 2024?"*).
* **Generación Automática de SQL:** Utiliza Google Gemini (LLM) para traducir preguntas de negocio a consultas SQL optimizadas para SQLite.
* **Lógica Financiera Integrada:**
    * Cálculo automático de **EBIT** (Ingresos - COGS - Gastos).
    * Normalización de nombres de países y monedas.
    * Manejo de escenarios (Real vs Plan).
* **Explicación de Resultados:** No solo entrega el dato, sino que genera una explicación breve y contextualizada del resultado.
* **Transparencia:** Opción para visualizar la query SQL generada para auditoría de datos.

## 🛠️ Tecnologías Utilizadas

* **Frontend:** [Streamlit](https://streamlit.io/) (Interfaz de chat interactiva).
* **IA Generativa:** Google Gemini (vía `google-generativeai`), priorizando modelos Flash/Pro para velocidad y precisión.
* **Base de Datos:** SQLite (`CFO_SAP_PYL.db`).
* **Procesamiento de Datos:** Pandas.

## ⚙️ Configuración Local

1.  **Clonar el repositorio:**
    ```bash
    git clone <tu-repositorio>
    cd <tu-carpeta>
    ```

2.  **Instalar dependencias:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configurar API Key:**
    Crea una carpeta `.streamlit` y un archivo `secrets.toml` dentro:
    ```toml
    [general]
    GOOGLE_API_KEY = "TU_API_KEY_DE_GOOGLE"
    ```

4.  **Ejecutar la aplicación:**
    ```bash
    streamlit run app.py
    ```

## ☁️ Despliegue en Streamlit Cloud

La aplicación está optimizada para correr en Streamlit Community Cloud:
1.  Sube el código a GitHub (asegúrate de incluir `requirements.txt`).
2.  Conecta tu repositorio en Streamlit Cloud.
3.  En la configuración avanzada ("Advanced Settings"), agrega tu API Key en la sección **Secrets**:
    ```toml
    [general]
    GOOGLE_API_KEY = "aiuaS..."
    ```
4.  Si la base de datos no está en el repositorio, la aplicación te pedirá subir el archivo `.db` mediante la barra lateral al iniciar.

---
*Desarrollado para simplificar el análisis financiero mediante IA Generativa.*

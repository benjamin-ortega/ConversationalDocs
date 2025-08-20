# Desafío Técnico: Copiloto Conversacional sobre Documentos

## Descripción del Proyecto

Este proyecto es un copiloto conversacional diseñado para interactuar con hasta 5 archivos PDF subidos por el usuario. La aplicación permite hacer preguntas en lenguaje natural sobre el contenido de los documentos, así como realizar tareas de análisis avanzado como resúmenes, comparaciones y clasificación automática por temas.

## Instrucciones para Levantar el Entorno

Para ejecutar la aplicación, tener **Docker** y **Docker Compose** instalados.

1.  **Configurar la API Key:**
    Crea un archivo .env en la raíz del proyecto y añade tu clave de la API de Google Gemini

    Para obtener tu clave: Ve a Google AI Studio y sigue las instrucciones para crear una nueva clave de API.

    ```env
    GEMINI_API_KEY=tu_clave_de_api_aqui
    ```

2.  **Levantar la aplicación con Docker Compose:**
    Ejecuta el siguiente comando para construir la imagen y arrancar el contenedor.

    ```bash
    docker compose up --build
    ```

3.  **Acceder a la aplicación:**
    Abre tu navegador y navega a la siguiente URL:
    [http://localhost:8501]

---

## Arquitectura del Sistema

El sistema sigue una arquitectura modular y estructurada, dividida en un **backend** (lógica de procesamiento) y un **frontend** (interfaz de usuario).

1.  **Frontend (app.py):**
    Construido con **Streamlit**, provee la interfaz para la interacción del usuario. Gestiona la subida de archivos, el flujo conversacional y las opciones de análisis avanzado a través de botones y selectores. El estado de la aplicación se mantiene en `st.session_state`.

2.  **Backend (core/backend.py):**
    Contiene toda la lógica de negocio y las integraciones, funcionando como el motor del sistema. Se encarga de:
    - **Procesamiento de Documentos:** Utiliza la librería `PyMuPDFLoader` para cargar los PDFs. El texto extraído se divide en fragmentos manejables con `RecursiveCharacterTextSplitter`.
    - **Almacenamiento Vectorial:** Emplea **ChromaDB** para almacenar los **embeddings** (representaciones numéricas) de los fragmentos de texto, lo que permite una búsqueda semántica eficiente. Los embeddings se generan con `GoogleGenerativeAIEmbeddings`.
    - **Orquestación del LLM:** Usa **LangChain** como un framework de orquestación. Para el chat conversacional, se implementa una `ConversationalRetrievalChain` que gestiona el flujo de la pregunta, la recuperación de contexto y la generación de la respuesta.
    - **Modelo de Lenguaje (LLM):** La API de **Gemini 1.5 Pro** se usa para la generación de respuestas. Una clase personalizada, `GeminiAPIWrapper`, encapsula la lógica de la API para mantener el código limpio y modular.

---

## Justificación de Elecciones Técnicas

- **Python + Streamlit:** Proporciona un stack de desarrollo rápido para prototipos de IA, permitiendo construir una interfaz funcional en poco tiempo.
- **LangChain:** Es un framework de orquestación maduro y flexible. Sus "chains" y "retrievers" permiten una estructura clara y un flujo de trabajo extensible, facilitando la adición de nuevas funcionalidades.
- **ChromaDB:** Un vector store ligero y de código abierto que se integra fácilmente con LangChain. Su naturaleza "en memoria" (por defecto) es ideal para este tipo de desafío donde los datos no necesitan persistir entre sesiones.
- **Google Gemini 1.5 Pro:** Elegido por su rendimiento avanzado en razonamiento complejo y la capacidad de manejar grandes contextos, lo que es crucial para analizar documentos extensos. La implementación de una clase `GeminiAPIWrapper` encapsula la lógica de la API, manteniendo el código limpio y desacoplado.
- **Docker + Docker Compose:** Garantiza que el entorno de la aplicación sea reproducible en cualquier máquina. Simplifica la configuración de dependencias, la API key y el arranque del servicio.

---

## Flujo Conversacional

El flujo sigue un ciclo simple de "Pregunta -> Búsqueda -> Respuesta".

1.  **Vectorización de Documentos:** Al procesar los PDFs, el contenido se divide en fragmentos y se convierte en representaciones numéricas (`embeddings`) que se almacenan en el `vectorstore` (ChromaDB).
2.  **Pregunta del Usuario:** El usuario introduce una pregunta en la interfaz de chat.
3.  **Búsqueda de Contexto:** La cadena conversacional utiliza el `vectorstore` para encontrar los fragmentos de texto más relevantes para la pregunta del usuario. Se consideran tanto la pregunta actual como el historial de la conversación.
4.  **Generación de Respuesta:** La pregunta y los fragmentos de texto relevantes se envían a la API de Google Gemini como un solo prompt. El LLM utiliza este contexto para generar una respuesta coherente y precisa.
5.  **Historial y Memoria:** La `ConversationBufferMemory` de LangChain almacena el historial del chat para que las respuestas futuras sean más contextuales y mantengan el hilo de la conversación.

---

## Limitaciones y Mejoras Futuras

- **Escalabilidad:** El `vectorstore` actual (ChromaDB en memoria) no es escalable para un gran volumen de documentos o usuarios. Una mejora sería migrar a una solución de nube como Weaviate o Qdrant.
- **Manejo de Errores:** Aunque se manejan errores de la API, se podrían añadir más validaciones y mensajes de error más específicos para una mejor experiencia de usuario.
- **Tipos de Archivos:** Actualmente solo se aceptan PDFs. Se podría extender la funcionalidad para incluir otros formatos como `.docx` o `.txt`.

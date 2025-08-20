API_ERROR_MESSAGE = "Clave de API no encontrada en las variables de entorno."
API_NO_RESPONSE_MESSAGE = "No se pudo obtener una respuesta de la API."
DOCUMENT_NOT_FOUND_MESSAGE = "No se pudo encontrar el contenido del documento '{doc_name}'."


DOCUMENT_TOPICS = [
    "Negocios y Finanzas", 
    "Ciencia y Tecnología", 
    "Salud y Medicina", 
    "Arte y Cultura", 
    "Política y Sociedad",
    "Otros"
]

DOCUMENT_PROMPTS = {
    "chat_prompt_template": (
        "Eres un útil asistente de preguntas y respuestas. Usa las siguientes partes de contexto "
        "recuperado para responder a la pregunta. Si no sabes la respuesta, solo di que no la sabes. "
        "No intentes inventar una respuesta. Mantén tu respuesta concisa. Responde siempre en español.\n"
        "Historial del chat: {chat_history}\n"
        "Pregunta: {question}\n"
        "Contexto: {context}\n"
        "Respuesta:"
    ),
    "topic_classification": (
        "Clasifica el siguiente texto con un tema de la lista: {topics_list_str}. "
        "La respuesta debe ser solo el nombre del tema y en español.\n"
        "EJEMPLO:\n"
        "Texto: 'El informe financiero trimestral muestra un crecimiento del 5%.'\n"
        "Tema: 'Negocios y Finanzas'\n\n"
        "Texto: '{doc_text}'\n"
        "Resultado:"
    ),
    "summary": "Por favor, proporciona un resumen conciso del siguiente documento en español: '{full_text}'",
    "comparison": (
        "Compara los siguientes dos textos e identifica sus similitudes y diferencias "
        "en un resumen bien estructurado y en español.\n\n"
        "Documento 1:\n{doc1_text}\n\n"
        "Documento 2:\n{doc2_text}"
    )
}

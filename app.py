import streamlit as st
import os
import shutil
from core.backend import get_vectorstore_from_docs, get_conversational_chain, get_document_topics, get_document_summary, compare_documents

def setup_page():
    st.set_page_config(page_title="PDF Chatbot", page_icon=":books:")
    st.title("📚 PDF Chatbot")

def initialize_session_state():
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "conversation_chain" not in st.session_state:
        st.session_state.conversation_chain = None
    if "vectorstore" not in st.session_state:
        st.session_state.vectorstore = None

def display_chat_messages():
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

def handle_pdf_processing(pdf_files):
    if not pdf_files:
        st.warning("Por favor, sube al menos un archivo PDF.")
        return False
    elif len(pdf_files) > 5:
        st.warning("Por favor, sube un máximo de 5 archivos PDF.")
        return False
    else:
        with st.spinner("Procesando PDFs..."):
            temp_dir = "temp_pdfs"
            
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            os.makedirs(temp_dir)

            pdf_paths = []
            for pdf_file in pdf_files:
                pdf_path = os.path.join(temp_dir, pdf_file.name)
                with open(pdf_path, "wb") as f:
                    f.write(pdf_file.getbuffer())
                pdf_paths.append(pdf_path) 
            
            try:
                st.session_state.vectorstore = get_vectorstore_from_docs(pdf_paths)
                st.session_state.conversation_chain = get_conversational_chain(st.session_state.vectorstore)
                st.session_state.messages = []
                st.success("PDFs procesados correctamente. ¡Ahora puedes hacer preguntas!")
                return True
            except Exception as e:
                st.error(f"Ocurrió un error al procesar los PDFs: {e}")
                return False
            finally:
                shutil.rmtree(temp_dir, ignore_errors=True)
                

def handle_sidebar():
    with st.sidebar:
        st.header("PDF")
        pdf_files = st.file_uploader(
            "Hasta 5 PDF",
            type=["pdf"],
            accept_multiple_files=True
        )
        if st.button("Procesar PDF"):
            handle_pdf_processing(pdf_files)

def handle_chat_input():
    if prompt := st.chat_input("¿Cómo puedo ayudarte?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            if st.session_state.conversation_chain:
                with st.spinner("Generando respuesta..."):
                    response = st.session_state.conversation_chain({"question": prompt})
                    st.markdown(response["answer"])
                    st.session_state.messages.append({"role": "assistant", "content": response["answer"]})
            else:
                st.error("Por favor, procesa los PDFs primero.")

def get_document_sources():
    if not st.session_state.get("vectorstore"):
        return []
    
    doc_sources = []
    all_documents = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 100}).get_relevant_documents("")
    for doc in all_documents:
        source = os.path.basename(doc.metadata.get("source", ""))
        if source and source not in doc_sources:
            doc_sources.append(source)
    return doc_sources

def render_document_summary_section(doc_sources):
    st.subheader("Resumen de un Documento")
    if doc_sources:
        selected_doc_name = st.selectbox("Selecciona un documento para resumir:", doc_sources)
        if st.button("Generar Resumen"):
            if selected_doc_name:
                with st.spinner("Generando resumen del contenido..."):
                    summary = get_document_summary(st.session_state.vectorstore, selected_doc_name)
                    st.write(f"### Resumen de '{selected_doc_name}':")
                    st.markdown(summary)
            else:
                st.warning("Por favor, selecciona un documento para resumir.")
    else:
        st.info("Por favor, procesa los PDFs primero para activar esta funcionalidad.")

def render_document_classification_section():
    if st.session_state.get("vectorstore"):
        st.subheader("Clasificar Documentos")
        if st.button("Clasificar"):
            with st.spinner("Clasificando documentos..."):
                classified_documents = get_document_topics(st.session_state.vectorstore)
                st.write("### Resultados de la Clasificación:")
                for doc_title, doc_topic in classified_documents:
                    st.write(f"**Documento:** {doc_title} - **Tema:** {doc_topic}")
    else:
        st.info("Por favor, procesa los PDFs primero para activar esta funcionalidad.")


def render_document_comparison_section(doc_sources):
    st.subheader("Comparar dos Documentos")
    if doc_sources and len(doc_sources) >= 2:
        col1, col2 = st.columns(2)
        with col1:
            doc1 = st.selectbox("Selecciona el primer documento", doc_sources, key="doc1_select")
        with col2:
            doc2 = st.selectbox("Selecciona el segundo documento", doc_sources, key="doc2_select", index=len(doc_sources) - 1 if len(doc_sources) > 1 else 0)
        
        if st.button("Comparar"):
            if doc1 and doc2 and doc1 != doc2:
                with st.spinner(f"Comparando {doc1} y {doc2}..."):
                    comparison_result = compare_documents(st.session_state.vectorstore, doc1, doc2)
                    st.markdown(comparison_result)
            else:
                st.warning("Por favor, selecciona dos documentos diferentes para comparar.")
    else:
        st.info("Por favor, procesa al menos dos PDFs para activar esta funcionalidad.")

def main():
    setup_page()
    initialize_session_state()
    
    handle_sidebar()
    display_chat_messages()
    handle_chat_input()

    doc_sources = get_document_sources()

    if st.session_state.get("vectorstore"):
        render_document_summary_section(doc_sources)
        render_document_classification_section()
        render_document_comparison_section(doc_sources)
    else:
        st.info("Procesa los PDFs para ver las herramientas de análisis de documentos.")


if __name__ == "__main__":
    main()
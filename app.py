import os
import tempfile
from dotenv import load_dotenv
import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.chains import RetrievalQA

load_dotenv()

st.set_page_config(page_title="📄 RAG PDF Chat", layout="wide")
st.title("🤖 Chat with Your PDF")

# Sidebar for file upload
st.sidebar.header("📁 Upload PDF")
pdf_file = st.sidebar.file_uploader("Choose a PDF file", type="pdf")

@st.cache_resource(show_spinner="🔍 Processing PDF...")
def process_pdf(file):
    # Read text from PDF
    pdf_reader = PdfReader(file)
    raw_text = ""
    for page in pdf_reader.pages:
        page_text = page.extract_text()
        if page_text:
            raw_text += page_text

    if not raw_text.strip():
        raise ValueError("❌ No extractable text found in the PDF.")

    # Chunk text
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    chunks = splitter.split_text(raw_text)

    if not chunks:
        raise ValueError("❌ Text splitting failed. No chunks were created.")

    # Embed and store in FAISS
    embeddings = OpenAIEmbeddings()
    vector_store = FAISS.from_texts(chunks, embedding=embeddings)

    return vector_store

# Initialize vector store
if pdf_file:
    try:
        with st.spinner("🔧 Processing..."):
            vector_store = process_pdf(pdf_file)
            retriever = vector_store.as_retriever(search_kwargs={"k": 3})
            qa_chain = RetrievalQA.from_chain_type(
                llm=ChatOpenAI(temperature=0),
                retriever=retriever
            )

        st.success("✅ PDF processed! Ask your questions below.")
        st.subheader("💬 Ask Questions")
        query = st.text_input("Type your question here...")

        if query:
            with st.spinner("🧠 Thinking..."):
                response = qa_chain.invoke(query)
                st.success(response)

    except Exception as e:
        st.error(str(e))
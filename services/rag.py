from langchain.embeddings import HuggingFaceEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.document_loaders import PyPDFLoader
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA
import os
from dotenv import load_dotenv
import pickle
from utils.prompts import RETRIEVAL_PROMPT

load_dotenv()

# Global vars
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")
vectorstore = None
qa_chain = None

def build_index():
    global vectorstore, qa_chain
    documents = []
    
    # Load PDFs
    for pdf in os.listdir("documents"):
        if pdf.endswith(".pdf"):
            loader = PyPDFLoader(f"documents/{pdf}")
            docs = loader.load()
            splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            chunks = splitter.split_documents(docs)
            documents.extend(chunks)
    
    # Embed and index
    vectorstore = FAISS.from_documents(documents, embeddings)
    vectorstore.save_local("vectorstore/faiss_index")
    
    # Setup QA chain
    llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama3-8b-8192")
    prompt = PromptTemplate(template=RETRIEVAL_PROMPT, input_variables=["context", "question", "language"])
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever(search_kwargs={"k": 3}),
        chain_type_kwargs={"prompt": prompt}
    )
    print("Index built! Loaded", len(documents), "chunks.")

def load_index():
    global vectorstore, qa_chain
    if os.path.exists("vectorstore/faiss_index"):
        vectorstore = FAISS.load_local("vectorstore/faiss_index", embeddings, allow_dangerous_deserialization=True)
        # Re-init QA (simple for MVP)
        llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model_name="llama3-8b-8192")
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            chain_type="stuff",
            retriever=vectorstore.as_retriever(search_kwargs={"k": 3})
        )
        print("Index loaded!")

def get_rag_response(question: str, language: str = "English"):
    if qa_chain is None:
        load_index()
    
    result = qa_chain({"query": question})
    score = max([doc.metadata.get("score", 0) for doc in result["source_documents"]]) if result["source_documents"] else 0
    
    if score < 0.75:
        return {"answer": "I don't have verified information on that. Try asking about the Constitution or Vision 2030.", "score": score, "citations": []}
    
    citations = [doc.metadata.get("source", "Unknown") for doc in result["source_documents"]]
    return {"answer": result["result"], "score": score, "citations": citations}
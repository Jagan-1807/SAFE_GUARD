import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.llms.openrouter import OpenRouter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb
from dotenv import load_dotenv

load_dotenv()

# Configure LLM (OpenRouter) and Embedding (Local HF)
api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    llm = OpenRouter(
        model="google/gemini-2.0-flash-001",
        api_key=api_key
    )
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    DEMO_MODE = False
else:
    llm = None
    embed_model = None
    DEMO_MODE = True

def get_index():
    # Initialize ChromaDB
    db = chromadb.PersistentClient(path="./chroma_db")
    chroma_collection = db.get_or_create_collection("support_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Check if index exists or create new
    if chroma_collection.count() == 0:
        documents = SimpleDirectoryReader("../docs").load_data()
        parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = parser.get_nodes_from_documents(documents)
        index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)
    else:
        index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    
    return index

def get_query_engine():
    index = get_index()
    return index.as_query_engine(llm=llm, similarity_top_k=3)

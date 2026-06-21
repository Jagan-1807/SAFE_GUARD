import os
from llama_index.core import VectorStoreIndex, SimpleDirectoryReader, StorageContext
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core.node_parser import SentenceSplitter
import chromadb
from dotenv import load_dotenv

load_dotenv()

# Resolve paths relative to this file's location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")
DOCS_PATH = os.path.join(BASE_DIR, "..", "docs")

# Configure Embedding (Local HF)
api_key = os.getenv("OPENROUTER_API_KEY")
if api_key:
    embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")
    DEMO_MODE = False
else:
    embed_model = None
    DEMO_MODE = True

def get_index():
    # Initialize ChromaDB
    db = chromadb.PersistentClient(path=CHROMA_DB_PATH)
    chroma_collection = db.get_or_create_collection("support_docs")
    vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
    storage_context = StorageContext.from_defaults(vector_store=vector_store)

    # Check if index exists or create new
    if chroma_collection.count() == 0:
        documents = SimpleDirectoryReader(DOCS_PATH).load_data()
        parser = SentenceSplitter(chunk_size=512, chunk_overlap=50)
        nodes = parser.get_nodes_from_documents(documents)
        index = VectorStoreIndex(nodes, storage_context=storage_context, embed_model=embed_model)
    else:
        index = VectorStoreIndex.from_vector_store(vector_store, embed_model=embed_model)
    
    return index

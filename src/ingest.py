import os
import time
import certifi
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_postgres import PGVector

# Carrega variáveis de ambiente
load_dotenv()

PDF_PATH = os.getenv("PDF_PATH")

# Configura certificados confiáveis
os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()

def get_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
    # Gemini API changed model naming; keep legacy env value working.
    if model == "models/embedding-001":
        model = "models/gemini-embedding-001"
    return GoogleGenerativeAIEmbeddings(model=model)


def _is_quota_or_rate_limit_error(err: Exception) -> bool:
    msg = str(err).lower()
    return "429" in msg or "resourceexhausted" in msg or "quota" in msg


def add_documents_with_retry(store: PGVector, documents: list[Document], ids: list[str]) -> None:
    batch_size = int(os.getenv("INGEST_BATCH_SIZE", "4"))
    max_retries = int(os.getenv("INGEST_MAX_RETRIES", "5"))
    base_delay = float(os.getenv("INGEST_RETRY_DELAY_SECONDS", "8"))

    for start in range(0, len(documents), batch_size):
        end = start + batch_size
        docs_batch = documents[start:end]
        ids_batch = ids[start:end]

        for attempt in range(max_retries + 1):
            try:
                store.add_documents(documents=docs_batch, ids=ids_batch)
                print(f"Lote {start // batch_size + 1}: {len(docs_batch)} docs inseridos.")
                break
            except Exception as err:
                if not _is_quota_or_rate_limit_error(err) or attempt == max_retries:
                    raise
                sleep_s = base_delay * (2 ** attempt)
                print(f"Rate limit/quota detectado. Tentando novamente em {sleep_s:.1f}s...")
                time.sleep(sleep_s)

def ingest_pdf():
    # Verifica variáveis obrigatórias
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env")
    for k in ("DATABASE_URL", "PG_VECTOR_COLLECTION_NAME"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")

    # Carrega PDF
    docs = PyPDFLoader(str(PDF_PATH)).load()

    # Divide em chunks
    splits = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=150,
        add_start_index=False
    ).split_documents(docs)

    if not splits:
        raise SystemExit("Nenhum conteúdo encontrado no PDF.")

    # Cria documentos enriquecidos
    enriched = [
        Document(
            page_content=d.page_content,
            metadata={k: v for k, v in d.metadata.items() if v not in ("", None)}
        )
        for d in splits
    ]

    ids = [f"doc-{i}" for i in range(len(enriched))]

    # Conecta ao Postgres vector store
    store = PGVector(
        embeddings=get_embeddings(),
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )

    # Adiciona documentos em lotes para reduzir 429 e respeitar limites da API.
    add_documents_with_retry(store, enriched, ids)
    print(f"Ingestão concluída: {len(enriched)} documentos adicionados.")

if __name__ == "__main__":
    ingest_pdf()
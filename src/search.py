import os
from dotenv import load_dotenv

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_postgres import PGVector
from langchain_core.prompts import PromptTemplate

load_dotenv()

PROMPT_TEMPLATE = """
CONTEXTO:
{contexto}

REGRAS:
- Responda somente com base no CONTEXTO.
- Se a informação não estiver explicitamente no CONTEXTO, responda:
  "Não tenho informações necessárias para responder sua pergunta."
- Nunca invente ou use conhecimento externo.
- Nunca produza opiniões ou interpretações além do que está escrito.
- Sempre responda em frases completas e naturais, como se estivesse conversando.

EXEMPLOS DE RESPOSTAS:
Pergunta: "Qual o faturamento da Empresa SuperTechIABrazil?"
Resposta: "O faturamento da Empresa SuperTechIABrazil foi de 10 milhões de reais."

Pergunta: "Qual é a capital da França?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Quantos clientes temos em 2024?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

Pergunta: "Você acha isso bom ou ruim?"
Resposta: "Não tenho informações necessárias para responder sua pergunta."

PERGUNTA DO USUÁRIO:
{pergunta}

RESPONDA A "PERGUNTA DO USUÁRIO" EM UMA FRASE COMPLETA
"""

def get_embeddings():
    if os.getenv("OPENAI_API_KEY"):
        return OpenAIEmbeddings(model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"))
    model = os.getenv("GOOGLE_EMBEDDING_MODEL", "models/embedding-001")
    # Gemini API changed model naming; keep legacy env value working.
    if model == "models/embedding-001":
        model = "models/gemini-embedding-001"
    return GoogleGenerativeAIEmbeddings(model=model)

def get_llm():
    if os.getenv("OPENAI_API_KEY"):
        return ChatOpenAI(model=os.getenv("OPENAI_LLM_MODEL", "gpt-5-nano"))
    return ChatGoogleGenerativeAI(model=os.getenv("GOOGLE_LLM_MODEL", "gemini-2.5-flash-lite"))

def search_prompt(question=None):
    if not os.getenv("OPENAI_API_KEY") and not os.getenv("GOOGLE_API_KEY"):
        raise RuntimeError("Defina OPENAI_API_KEY ou GOOGLE_API_KEY no .env")
    for k in ("DATABASE_URL", "PG_VECTOR_COLLECTION_NAME"):
        if not os.getenv(k):
            raise RuntimeError(f"Environment variable {k} is not set")

    if not question:
        return None

    # Buscar top 10 resultados no banco vetorial
    store = PGVector(
        embeddings=get_embeddings(),
        collection_name=os.getenv("PG_VECTOR_COLLECTION_NAME"),
        connection=os.getenv("DATABASE_URL"),
        use_jsonb=True,
    )
    docs = store.similarity_search_with_score(question, k=10)
    contexto = "\n\n".join([d[0].page_content for d in docs])

    # Montar prompt
    question_template = PromptTemplate(
        input_variables=["contexto", "pergunta"],
        template=PROMPT_TEMPLATE
    ).format(contexto=contexto, pergunta=question)

    response = get_llm().invoke(question_template)
    return response.content if hasattr(response, 'content') else response
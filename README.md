# Desafio MBA Engenharia de Software com IA - Full Cycle

Projeto de RAG com:
- ingestao de PDF para `pgvector` (PostgreSQL)
- busca semantica
- chat com contexto do documento

## 1) Pre-requisitos

- Docker
- Docker Compose (`docker-compose`)

## 2) Configuracao do `.env`

Use o arquivo `.env` na raiz do projeto. Voce pode usar **Google Gemini** ou **OpenAI**.

### Opcao A - Google Gemini

- `GOOGLE_API_KEY`: chave da Gemini API
- `GOOGLE_EMBEDDING_MODEL=models/embedding-001`
- `GOOGLE_LLM_MODEL=gemini-2.5-flash-lite`

### Opcao B - OpenAI

- `OPENAI_API_KEY`: chave da OpenAI API
- `OPENAI_EMBEDDING_MODEL=text-embedding-3-small`
- `OPENAI_LLM_MODEL=gpt-5-nano`

### Variaveis obrigatorias em qualquer opcao

- `DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/rag`
- `PG_VECTOR_COLLECTION_NAME=documents`
- `PDF_PATH=/app/document.pdf`

> Importante: deixe preenchida apenas a opcao de provedor que voce quer usar no momento.

## 3) Subir containers

No primeiro uso (ou quando mudar dependencias):

```bash
docker-compose build --no-cache app
docker-compose up -d
```

Nos proximos usos:

```bash
docker-compose up -d
```

## 4) Ingestao do PDF

Rode a ingestao para popular o vetor store:

```bash
docker-compose exec app python3 src/ingest.py
```

Se ocorrer erro de cota/rate limit (429), rode com lote menor:

```bash
docker-compose exec app env INGEST_BATCH_SIZE=1 INGEST_MAX_RETRIES=8 INGEST_RETRY_DELAY_SECONDS=12 python3 src/ingest.py
```

## 5) Executar o chat

### Modo interativo

```bash
docker-compose exec -it app python3 src/chat.py
```

### Pergunta direta por argumento

```bash
docker-compose exec app python3 src/chat.py "Qual e o assunto principal do documento?"
```

## 6) Fluxo rapido (resumo)

```bash
docker-compose up -d
docker-compose exec app python3 src/ingest.py
docker-compose exec -it app python3 src/chat.py
```

## 7) Troubleshooting

- `429 ResourceExhausted`: cota/minuto/dia do provedor foi excedida; aguarde e tente novamente.
- `ModuleNotFoundError`: rebuild da imagem com `docker-compose build --no-cache app`.
- `Environment variable ... is not set`: revise o arquivo `.env`.
- Mudou `.env` e nao refletiu no container: execute `docker-compose up -d --force-recreate app`.

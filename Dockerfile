FROM python:3.11-slim

WORKDIR /app

# Instala torch CPU-only primeiro (evita baixar a versão GPU de ~2GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Instala demais dependências
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código-fonte, o PDF e o script de inicialização
COPY src/ ./src/
COPY document.pdf .
COPY start.sh .
RUN chmod +x start.sh

# Mantém o container rodando para uso interativo (conforme README)
CMD ["bash"]

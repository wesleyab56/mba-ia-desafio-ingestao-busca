#!/bin/bash
set -e  # Para o script falhar se algum comando der erro

# Primeiro, ingere os PDFs
python src/ingest.py

# Depois, executa o chat
python src/chat.py
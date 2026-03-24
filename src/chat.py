from search import search_prompt

def main():
    import sys
    if len(sys.argv) < 2:
        question = input("Faça sua pergunta:\n\nPERGUNTA: ")
    else:
        question = sys.argv[1]
    resposta = search_prompt(question)
    if not resposta:
        print("Não foi possível obter resposta. Verifique as configurações.")
        return
    print("RESPOSTA: " + resposta)

if __name__ == "__main__":
    main()
import google.generativeai as genai
import os
from chaves import GEMINI_API_KEY

# Configure sua chave de API
# É altamente recomendado usar variáveis de ambiente para a chave de API
# Por exemplo, defina a variável de ambiente GEMINI_API_KEY com sua chave
genai.configure(api_key=GEMINI_API_KEY)

# Ou, se estiver apenas testando e não se importar em expor a chave (NÃO RECOMENDADO PARA PRODUÇÃO):
# genai.configure(api_key="SUA_CHAVE_DE_API_AQUI")

# Escolha o modelo que você quer usar
# 'gemini-2.0-flash' é o que você estava tentando usar no curl
model = genai.GenerativeModel('gemini-2.0-flash')

# Defina o conteúdo da sua requisição
prompt = "Explain how AI works in a few words"

try:
    # Gerar o conteúdo
    response = model.generate_content(prompt)

    # Imprimir a resposta
    print(response.text)

except Exception as e:
    print(f"Ocorreu um erro: {e}")
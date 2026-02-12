
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:10]}...")

try:
    print("Tentando conectar...")
    client = create_client(url, key)
    print("Client criado.")
    
    print("Tentando listar categorias...")
    response = client.table("categorias").select("*").execute()
    print("Sucesso!")
    print(response.data)
except Exception as e:
    print("ERRO:")
    print(e)

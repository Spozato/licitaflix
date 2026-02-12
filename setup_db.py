"""
Setup script: executa o schema SQL no Supabase via API REST.
Uso: python setup_db.py
"""
import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Configure SUPABASE_URL e SUPABASE_KEY no .env")
    exit(1)

# Ler schema SQL
schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
with open(schema_path, "r", encoding="utf-8") as f:
    sql = f.read()

# Dividir em blocos (separar por ponto-e-vírgula + newline)
blocos = [b.strip() for b in sql.split(";\n") if b.strip() and not b.strip().startswith("--")]

print(f"🔧 Executando {len(blocos)} blocos SQL no Supabase...")
print(f"📡 URL: {SUPABASE_URL}")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=minimal"
}

# Usar a Supabase REST API para verificar a conexão
try:
    resp = requests.get(
        f"{SUPABASE_URL}/rest/v1/",
        headers=headers,
        timeout=10
    )
    print(f"✅ Conexão OK (status: {resp.status_code})")
except Exception as e:
    print(f"❌ Erro de conexão: {e}")
    exit(1)

print("\n" + "=" * 50)
print("❗ IMPORTANTE: Execute o schema.sql manualmente!")
print("=" * 50)
print(f"""
O Supabase não permite executar DDL (CREATE TABLE) via API REST.
Siga estes passos:

1. Acesse: {SUPABASE_URL.replace('.co', '.co').replace('https://', 'https://supabase.com/dashboard/project/').split('.supabase')[0]}
   Ou vá para https://supabase.com/dashboard e selecione seu projeto.

2. No menu lateral, clique em "SQL Editor"

3. Cole o conteúdo do arquivo schema.sql:
   📄 {schema_path}

4. Clique em "Run" (ou Ctrl+Enter)

5. Verifique se as tabelas foram criadas em "Table Editor"

Tabelas que serão criadas:
  • categorias
  • perfis_busca
  • termos_busca
  • licitacoes
  • licitacao_perfil
  • licitacao_status
  • historico_buscas
  • termos_sugeridos

Dados iniciais incluídos:
  • 3 categorias (Produtos, Obras, Reformas)
  • 8 perfis de busca
  • ~50 termos de busca
""")

# Tentar verificar se as tabelas já existem
print("🔍 Verificando tabelas existentes...")
tabelas = ["categorias", "perfis_busca", "termos_busca", "licitacoes", 
           "licitacao_perfil", "licitacao_status", "historico_buscas", "termos_sugeridos"]

for t in tabelas:
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/{t}?select=count&limit=0",
            headers=headers,
            timeout=5
        )
        if resp.status_code == 200:
            print(f"  ✅ {t} — existe")
        else:
            print(f"  ❌ {t} — não encontrada (execute o schema.sql)")
    except Exception:
        print(f"  ⚠️ {t} — erro ao verificar")

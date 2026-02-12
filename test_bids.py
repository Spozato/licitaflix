
from services import supabase_client as db

try:
    print("Tentando listar licitações...")
    bids = db.listar_licitacoes()
    print(f"Sucesso! Encontradas: {len(bids)}")
    print(bids)
except Exception as e:
    print("ERRO:")
    print(e)

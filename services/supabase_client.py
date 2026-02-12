"""
Licitaflix — Supabase Client
Conexão e operações CRUD com o banco Supabase.
"""
import os
import streamlit as st
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()


def get_client() -> Client:
    """Retorna instância do Supabase client (com cache do Streamlit)."""
    # Tenta carregar do .env primeiro
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

    # Se não encontrar, tenta st.secrets (para Streamlit Cloud)
    if not url:
        try:
            url = st.secrets["SUPABASE_URL"]
        except (FileNotFoundError, KeyError):
            pass
            
    if not key:
        try:
            key = st.secrets["SUPABASE_KEY"]
        except (FileNotFoundError, KeyError):
            pass

    if not url or not key:
        raise ValueError("SUPABASE_URL e SUPABASE_KEY devem ser configurados no .env ou st.secrets")
    
    return create_client(url, key)


# ============================================
# CATEGORIAS
# ============================================

def listar_categorias(apenas_ativas: bool = True):
    sb = get_client()
    query = sb.table("categorias").select("*").order("nome")
    if apenas_ativas:
        query = query.eq("ativa", True)
    return query.execute().data


def criar_categoria(nome: str, icone: str = "📦", cor: str = "#E50914"):
    sb = get_client()
    return sb.table("categorias").insert({
        "nome": nome, "icone": icone, "cor": cor
    }).execute().data


# ============================================
# PERFIS DE BUSCA
# ============================================

def listar_perfis(categoria_id: str = None, apenas_ativos: bool = True):
    sb = get_client()
    query = sb.table("perfis_busca").select("*, categorias(nome, icone, cor)").order("nome")
    if categoria_id:
        query = query.eq("categoria_id", categoria_id)
    if apenas_ativos:
        query = query.eq("ativo", True)
    return query.execute().data


def listar_perfis_hoje():
    """Retorna perfis marcados para buscar hoje."""
    sb = get_client()
    return sb.table("perfis_busca").select(
        "*, categorias(nome, icone, cor), termos_busca(id, termo, ativo, score_relevancia)"
    ).eq("ativo", True).eq("buscar_hoje", True).order("nome").execute().data


def atualizar_buscar_hoje(perfil_id: str, buscar: bool):
    sb = get_client()
    return sb.table("perfis_busca").update(
        {"buscar_hoje": buscar}
    ).eq("id", perfil_id).execute()


def criar_perfil(nome: str, categoria_id: str, descricao: str = "",
                 valor_minimo: float = None, valor_maximo: float = None,
                 regioes: list = None, modalidades: list = None):
    sb = get_client()
    data = {"nome": nome, "categoria_id": categoria_id, "descricao": descricao}
    if valor_minimo is not None:
        data["valor_minimo"] = valor_minimo
    if valor_maximo is not None:
        data["valor_maximo"] = valor_maximo
    if regioes:
        data["regioes"] = regioes
    if modalidades:
        data["modalidades"] = modalidades
    return sb.table("perfis_busca").insert(data).execute().data


def atualizar_perfil(perfil_id: str, updates: dict):
    sb = get_client()
    return sb.table("perfis_busca").update(updates).eq("id", perfil_id).execute()


# ============================================
# TERMOS DE BUSCA
# ============================================

def listar_termos(perfil_id: str, apenas_ativos: bool = True):
    sb = get_client()
    query = sb.table("termos_busca").select("*").eq("perfil_id", perfil_id).order("score_relevancia", desc=True)
    if apenas_ativos:
        query = query.eq("ativo", True)
    return query.execute().data


def adicionar_termo(perfil_id: str, termo: str, origem: str = "manual"):
    sb = get_client()
    return sb.table("termos_busca").insert({
        "perfil_id": perfil_id, "termo": termo.lower().strip(), "origem": origem
    }).execute().data


def atualizar_termo(termo_id: str, updates: dict):
    sb = get_client()
    return sb.table("termos_busca").update(updates).eq("id", termo_id).execute()


# ============================================
# LICITAÇÕES
# ============================================

def salvar_licitacao(dados: dict):
    """Upsert de uma licitação (usa id_compra como chave única)."""
    sb = get_client()
    return sb.table("licitacoes").upsert(
        dados, on_conflict="id_compra"
    ).execute().data


def salvar_licitacoes_batch(lista: list):
    """Salva múltiplas licitações de uma vez."""
    sb = get_client()
    if not lista:
        return []
    return sb.table("licitacoes").upsert(
        lista, on_conflict="id_compra"
    ).execute().data


def listar_licitacoes(filtros: dict = None, limite: int = 50, pagina: int = 1):
    sb = get_client()
    offset = (pagina - 1) * limite
    query = sb.table("licitacoes").select(
        "*, licitacao_status(*), licitacao_perfil(*, perfis_busca(nome, categorias(nome, icone, cor)))"
    ).order("data_publicacao", desc=True).range(offset, offset + limite - 1)

    if filtros:
        if filtros.get("uf"):
            query = query.eq("uf", filtros["uf"])
        if filtros.get("modalidade"):
            query = query.eq("modalidade", filtros["modalidade"])
        if filtros.get("status"):
            pass  # Filter via join
        if filtros.get("busca_texto"):
            query = query.ilike("objeto", f"%{filtros['busca_texto']}%")
    return query.execute().data


def buscar_licitacao_por_id(licitacao_id: str):
    sb = get_client()
    result = sb.table("licitacoes").select(
        "*, licitacao_status(*), licitacao_perfil(*, perfis_busca(nome, categorias(nome, icone, cor)))"
    ).eq("id", licitacao_id).execute().data
    return result[0] if result else None


def contar_licitacoes_hoje():
    sb = get_client()
    from datetime import date
    hoje = date.today().isoformat()
    result = sb.table("licitacoes").select("id", count="exact").gte("created_at", hoje).execute()
    return result.count or 0


# ============================================
# LICITACAO-PERFIL (vínculo)
# ============================================

def vincular_licitacao_perfil(licitacao_id: str, perfil_id: str, termo: str, score: float):
    sb = get_client()
    try:
        return sb.table("licitacao_perfil").upsert({
            "licitacao_id": licitacao_id,
            "perfil_id": perfil_id,
            "termo_encontrado": termo,
            "score_match": score
        }, on_conflict="licitacao_id,perfil_id").execute().data
    except Exception:
        pass  # Ignora duplicatas


# ============================================
# STATUS DE LICITAÇÃO
# ============================================

def atualizar_status_licitacao(licitacao_id: str, status: str, prioridade: str = None, notas: str = None):
    sb = get_client()
    data = {"licitacao_id": licitacao_id, "status": status, "updated_at": "now()"}
    if prioridade:
        data["prioridade"] = prioridade
    if notas is not None:
        data["notas"] = notas
    return sb.table("licitacao_status").upsert(
        data, on_conflict="licitacao_id"
    ).execute().data


# ============================================
# HISTÓRICO DE BUSCAS
# ============================================

def registrar_busca(perfil_id: str, termo: str, total_resultados: int):
    sb = get_client()
    return sb.table("historico_buscas").insert({
        "perfil_id": perfil_id,
        "termo_usado": termo,
        "total_resultados": total_resultados
    }).execute().data


# ============================================
# TERMOS SUGERIDOS
# ============================================

def listar_sugestoes(perfil_id: str):
    sb = get_client()
    return sb.table("termos_sugeridos").select("*").eq(
        "perfil_id", perfil_id
    ).is_("aceito", "null").order("frequencia", desc=True).execute().data


def responder_sugestao(sugestao_id: str, aceitar: bool):
    sb = get_client()
    return sb.table("termos_sugeridos").update(
        {"aceito": aceitar}
    ).eq("id", sugestao_id).execute()

"""
Licitaflix — Search Engine
Motor de busca com fuzzy matching nos objetos das licitações.
"""
from datetime import date, timedelta
from fuzzywuzzy import fuzz
from services.api_client import ComprasGovClient, MODALIDADES
from services import supabase_client as db


class SearchEngine:
    """Motor de busca: consulta APIs → fuzzy match → salva no Supabase."""

    SCORE_EXATO = 100
    SCORE_MINIMO = 60  # Threshold para considerar um match

    def __init__(self):
        self.api = ComprasGovClient()

    def buscar_por_perfil(self, perfil: dict, dias_atras: int = 7, callback=None) -> dict:
        """
        Executa busca completa para um perfil.
        
        Args:
            perfil: dict com dados do perfil (incluindo termos_busca)
            dias_atras: quantos dias atrás buscar
            callback: função(msg, progresso) para reportar progresso
            
        Returns:
            dict com estatísticas da busca
        """
        termos = perfil.get("termos_busca", [])
        termos_ativos = [t for t in termos if t.get("ativo", True)]
        
        if not termos_ativos:
            return {"encontradas": 0, "novas": 0, "termos_usados": 0}

        data_fim = date.today().isoformat()
        data_inicio = (date.today() - timedelta(days=dias_atras)).isoformat()

        # Buscar licitações das APIs
        if callback:
            callback(f"Consultando APIs para '{perfil['nome']}'...", 0.1)

        licitacoes_raw = self._buscar_apis(
            data_inicio, data_fim,
            perfil.get("regioes", []),
            perfil.get("modalidades", [])
        )

        if callback:
            callback(f"Encontradas {len(licitacoes_raw)} licitações. Filtrando...", 0.5)

        # Fazer matching com os termos
        matches = []
        for lic in licitacoes_raw:
            objeto = (lic.get("objeto") or "").lower()
            if not objeto:
                continue

            melhor_score = 0
            melhor_termo = ""

            for t in termos_ativos:
                termo = t["termo"].lower()
                # Score combinado: partial ratio + token set ratio
                score_partial = fuzz.partial_ratio(termo, objeto)
                score_token = fuzz.token_set_ratio(termo, objeto)
                score = max(score_partial, score_token)

                if score > melhor_score:
                    melhor_score = score
                    melhor_termo = t["termo"]

            if melhor_score >= self.SCORE_MINIMO:
                matches.append({
                    "licitacao": lic,
                    "termo": melhor_termo,
                    "score": melhor_score / 100.0,
                    "termo_id": next(
                        (t["id"] for t in termos_ativos if t["termo"] == melhor_termo), None
                    )
                })

        if callback:
            callback(f"{len(matches)} licitações relevantes encontradas!", 0.7)

        # Salvar no Supabase
        novas = self._salvar_resultados(matches, perfil["id"])

        # Atualizar contadores do perfil
        db.atualizar_perfil(perfil["id"], {
            "ultima_busca": "now()",
            "total_encontradas": perfil.get("total_encontradas", 0) + len(matches)
        })

        # Atualizar contadores dos termos
        termos_encontrados = {}
        for m in matches:
            termos_encontrados[m["termo"]] = termos_encontrados.get(m["termo"], 0) + 1

        for t in termos_ativos:
            if t["termo"] in termos_encontrados:
                db.atualizar_termo(t["id"], {
                    "vezes_encontrado": t.get("vezes_encontrado", 0) + termos_encontrados[t["termo"]]
                })

        # Registrar busca no histórico
        for t in termos_ativos:
            count = termos_encontrados.get(t["termo"], 0)
            db.registrar_busca(perfil["id"], t["termo"], count)

        if callback:
            callback(f"✅ Concluído! {novas} novas licitações salvas.", 1.0)

        return {
            "encontradas": len(matches),
            "novas": novas,
            "termos_usados": len(termos_ativos),
            "total_api": len(licitacoes_raw),
        }

    def buscar_por_categoria(self, categoria_id: str, dias_atras: int = 7, callback=None) -> dict:
        """Busca em todos os perfis de uma categoria."""
        perfis = db.listar_perfis(categoria_id=categoria_id)
        # Carregar termos para cada perfil
        resultados = {"total_encontradas": 0, "total_novas": 0, "perfis": []}

        for i, perfil in enumerate(perfis):
            perfil["termos_busca"] = db.listar_termos(perfil["id"])
            if callback:
                callback(
                    f"Buscando perfil {i+1}/{len(perfis)}: {perfil['nome']}",
                    i / len(perfis)
                )
            r = self.buscar_por_perfil(perfil, dias_atras)
            resultados["total_encontradas"] += r["encontradas"]
            resultados["total_novas"] += r["novas"]
            resultados["perfis"].append({"nome": perfil["nome"], **r})

        return resultados

    def buscar_todos_hoje(self, dias_atras: int = 7, callback=None) -> dict:
        """Busca em todos os perfis marcados para buscar hoje."""
        perfis = db.listar_perfis_hoje()
        resultados = {"total_encontradas": 0, "total_novas": 0, "perfis": []}

        for i, perfil in enumerate(perfis):
            if callback:
                callback(
                    f"🔍 [{i+1}/{len(perfis)}] {perfil['nome']}...",
                    i / len(perfis)
                )
            r = self.buscar_por_perfil(perfil, dias_atras)
            resultados["total_encontradas"] += r["encontradas"]
            resultados["total_novas"] += r["novas"]
            resultados["perfis"].append({"nome": perfil["nome"], **r})

        return resultados

    def _buscar_apis(self, data_inicio: str, data_fim: str,
                     regioes: list = None, modalidades: list = None) -> list:
        """Busca licitações em todas as fontes da API."""
        todos = []

        # 1. Contratações Lei 14.133 (principal)
        try:
            mods = modalidades if modalidades else [1, 2, 6, 7]
            if regioes:
                for uf in regioes:
                    resultados = self.api.buscar_todas_modalidades_14133(
                        data_inicio, data_fim, uf=uf, modalidades=mods, max_pages=2
                    )
                    todos.extend(resultados)
            else:
                resultados = self.api.buscar_todas_modalidades_14133(
                    data_inicio, data_fim, modalidades=mods, max_pages=2
                )
                todos.extend(resultados)
        except Exception as e:
            print(f"Erro busca 14133: {e}")

        # 2. Pregões legado
        try:
            pregoes = self.api.buscar_pregoes(data_inicio, data_fim, max_pages=2)
            todos.extend(pregoes)
        except Exception as e:
            print(f"Erro busca pregões: {e}")

        # 3. Licitações legado
        try:
            licitacoes = self.api.buscar_licitacoes_legado(data_inicio, data_fim, max_pages=2)
            todos.extend(licitacoes)
        except Exception as e:
            print(f"Erro busca licitações legado: {e}")

        # Deduplicar por id_compra
        vistos = set()
        unicos = []
        for lic in todos:
            id_c = lic.get("id_compra", "")
            if id_c and id_c not in vistos:
                vistos.add(id_c)
                unicos.append(lic)
            elif not id_c:
                unicos.append(lic)

        return unicos

    def _salvar_resultados(self, matches: list, perfil_id: str) -> int:
        """Salva licitações e vínculos no Supabase. Retorna quantidade de novas."""
        novas = 0
        for m in matches:
            lic = m["licitacao"]
            # Remover dados_brutos para o upsert (serializamos separado)
            lic_save = {k: v for k, v in lic.items() if k != "dados_brutos"}
            # Converter dados_brutos para string se necessário
            if lic.get("dados_brutos"):
                import json
                lic_save["dados_brutos"] = json.dumps(lic["dados_brutos"], default=str)

            try:
                result = db.salvar_licitacao(lic_save)
                if result:
                    lic_id = result[0]["id"] if isinstance(result, list) and result else None
                    if lic_id:
                        novas += 1
                        # Vincular ao perfil
                        db.vincular_licitacao_perfil(
                            lic_id, perfil_id, m["termo"], m["score"]
                        )
                        # Criar status inicial
                        db.atualizar_status_licitacao(lic_id, "nova", self._calcular_prioridade(lic))
            except Exception as e:
                print(f"Erro salvando licitação: {e}")
                continue
        return novas

    def _calcular_prioridade(self, lic: dict) -> str:
        """Calcula prioridade com base em prazo e valor."""
        from datetime import datetime

        # Verificar prazo
        data_enc = lic.get("data_encerramento_proposta") or lic.get("data_abertura_proposta")
        if data_enc:
            try:
                if isinstance(data_enc, str):
                    dt = datetime.fromisoformat(data_enc.replace("Z", "+00:00"))
                else:
                    dt = data_enc
                dias_restantes = (dt.date() - date.today()).days if hasattr(dt, 'date') else 999

                if dias_restantes <= 3:
                    return "urgente"
                elif dias_restantes <= 7:
                    return "alta"
            except (ValueError, TypeError):
                pass

        # Verificar valor
        valor = lic.get("valor_estimado")
        if valor and valor > 500000:
            return "alta"

        return "normal"

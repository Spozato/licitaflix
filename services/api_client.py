"""
Licitaflix — API Client
Cliente para as APIs ComprasGov Dados Abertos e PNCP.
"""
import requests
import time
from datetime import date, timedelta
from typing import Optional


BASE_URL_COMPRAS = "https://dadosabertos.compras.gov.br"
BASE_URL_PNCP = "https://pncp.gov.br/api/consulta"

# Códigos de modalidade (Lei 14.133/2021)
MODALIDADES = {
    1: "Pregão Eletrônico",
    2: "Concorrência",
    3: "Concurso",
    4: "Leilão",
    5: "Diálogo Competitivo",
    6: "Dispensa de Licitação",
    7: "Inexigibilidade",
    8: "Manifestação de Interesse",
    9: "Pré-qualificação",
    10: "Credenciamento",
    12: "Leilão - Alienação",
    13: "Dispensa por Limite",
}

# UFs do Brasil
UFS = [
    "AC", "AL", "AP", "AM", "BA", "CE", "DF", "ES", "GO", "MA", "MT", "MS",
    "MG", "PA", "PB", "PR", "PE", "PI", "RJ", "RN", "RS", "RO", "RR", "SC",
    "SP", "SE", "TO"
]


class ComprasGovClient:
    """Cliente para API dadosabertos.compras.gov.br"""

    def __init__(self):
        self.base_url = BASE_URL_COMPRAS
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def _get(self, endpoint: str, params: dict, max_pages: int = 5) -> list:
        """Faz GET paginado e retorna todos os resultados."""
        all_results = []
        params.setdefault("pagina", 1)
        params.setdefault("tamanhoPagina", 50)

        for page in range(max_pages):
            params["pagina"] = page + 1
            try:
                resp = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params=params,
                    timeout=30
                )
                if resp.status_code != 200:
                    break
                data = resp.json()
                resultado = data.get("resultado", [])
                if not resultado:
                    break
                all_results.extend(resultado)

                paginas_restantes = data.get("paginasRestantes", 0)
                if paginas_restantes <= 0:
                    break

                time.sleep(0.5)  # Rate limiting
            except Exception as e:
                print(f"Erro API ComprasGov: {e}")
                break

        return all_results

    def buscar_licitacoes_legado(
        self,
        data_inicio: str,
        data_fim: str,
        uasg: int = None,
        modalidade: int = None,
        max_pages: int = 3
    ) -> list:
        """Busca licitações no módulo legado (Lei 8.666)."""
        params = {
            "data_publicacao_inicial": data_inicio,
            "data_publicacao_final": data_fim,
        }
        if uasg:
            params["uasg"] = uasg
        if modalidade:
            params["modalidade"] = modalidade

        resultados = self._get("/modulo-legado/1_consultarLicitacao", params, max_pages)
        return [self._normalizar_legado(r) for r in resultados]

    def buscar_pregoes(
        self,
        data_inicio: str,
        data_fim: str,
        uasg: int = None,
        max_pages: int = 3
    ) -> list:
        """Busca pregões no módulo legado."""
        params = {
            "dt_data_edital_inicial": data_inicio,
            "dt_data_edital_final": data_fim,
        }
        if uasg:
            params["co_uasg"] = uasg

        resultados = self._get("/modulo-legado/3_consultarPregoes", params, max_pages)
        return [self._normalizar_pregao(r) for r in resultados]

    def buscar_contratacoes_14133(
        self,
        data_inicio: str,
        data_fim: str,
        modalidade: int = 1,
        uf: str = None,
        max_pages: int = 3
    ) -> list:
        """Busca contratações sob a Lei 14.133/2021."""
        params = {
            "dataPublicacaoPncpInicial": data_inicio,
            "dataPublicacaoPncpFinal": data_fim,
            "codigoModalidade": modalidade,
        }
        if uf:
            params["unidadeOrgaoUfSigla"] = uf

        resultados = self._get(
            "/modulo-contratacoes/1_consultarContratacoes_PNCP_14133",
            params, max_pages
        )
        return [self._normalizar_14133(r) for r in resultados]

    def buscar_todas_modalidades_14133(
        self,
        data_inicio: str,
        data_fim: str,
        uf: str = None,
        modalidades: list = None,
        max_pages: int = 2
    ) -> list:
        """Busca em todas as modalidades da 14.133 (ou nas especificadas)."""
        if modalidades is None:
            modalidades = [1, 2, 6, 7]  # Pregão, Concorrência, Dispensa, Inexigibilidade

        todos = []
        for mod in modalidades:
            try:
                resultados = self.buscar_contratacoes_14133(
                    data_inicio, data_fim, mod, uf, max_pages
                )
                todos.extend(resultados)
                time.sleep(0.3)
            except Exception as e:
                print(f"Erro modalidade {mod}: {e}")
                continue
        return todos

    # ========================================
    # Normalização (padronizar campos)
    # ========================================

    def _normalizar_legado(self, raw: dict) -> dict:
        return {
            "id_compra": raw.get("id_compra", ""),
            "numero_controle_pncp": None,
            "fonte": "comprasgov_legado",
            "modalidade": raw.get("nome_modalidade", ""),
            "modalidade_codigo": raw.get("modalidade"),
            "objeto": raw.get("objeto", "") or "",
            "valor_estimado": raw.get("valor_estimado_total"),
            "valor_homologado": raw.get("valor_homologado_total"),
            "orgao": None,
            "uasg": str(raw.get("uasg", "")),
            "uf": None,
            "municipio": None,
            "situacao": raw.get("situacao_aviso", ""),
            "data_publicacao": raw.get("data_publicacao"),
            "data_abertura_proposta": raw.get("data_abertura_proposta"),
            "data_encerramento_proposta": None,
            "data_resultado": None,
            "numero_itens": raw.get("numero_itens"),
            "numero_processo": raw.get("numero_processo", ""),
            "srp": False,
            "dados_brutos": raw,
        }

    def _normalizar_pregao(self, raw: dict) -> dict:
        return {
            "id_compra": raw.get("id_compra", ""),
            "numero_controle_pncp": None,
            "fonte": "comprasgov_pregao",
            "modalidade": "Pregão",
            "modalidade_codigo": None,
            "objeto": raw.get("tx_objeto", "") or "",
            "valor_estimado": self._parse_float(raw.get("vl_estimado_total")),
            "valor_homologado": self._parse_float(raw.get("vl_homologado_total")),
            "orgao": raw.get("no_orgao", ""),
            "uasg": str(raw.get("co_uasg", "")),
            "uf": None,
            "municipio": None,
            "situacao": raw.get("ds_situacao_pregao", ""),
            "data_publicacao": raw.get("dt_data_edital"),
            "data_abertura_proposta": raw.get("dt_inicio_proposta"),
            "data_encerramento_proposta": raw.get("dt_fim_proposta"),
            "data_resultado": raw.get("dt_resultado"),
            "numero_itens": None,
            "numero_processo": raw.get("co_processo", ""),
            "srp": False,
            "dados_brutos": raw,
        }

    def _normalizar_14133(self, raw: dict) -> dict:
        return {
            "id_compra": raw.get("idCompra", ""),
            "numero_controle_pncp": raw.get("numeroControlePNCP", ""),
            "fonte": "comprasgov_14133",
            "modalidade": raw.get("modalidadeNome", ""),
            "modalidade_codigo": raw.get("codigoModalidade"),
            "objeto": raw.get("objetoCompra", "") or "",
            "valor_estimado": raw.get("valorTotalEstimado"),
            "valor_homologado": raw.get("valorTotalHomologado"),
            "orgao": raw.get("orgaoEntidadeRazaoSocial", ""),
            "uasg": raw.get("unidadeOrgaoCodigoUnidade", ""),
            "uf": raw.get("unidadeOrgaoUfSigla", ""),
            "municipio": raw.get("unidadeOrgaoMunicipioNome", ""),
            "situacao": raw.get("situacaoCompraNomePncp", ""),
            "data_publicacao": self._extract_date(raw.get("dataPublicacaoPncp")),
            "data_abertura_proposta": raw.get("dataAberturaPropostaPncp"),
            "data_encerramento_proposta": raw.get("dataEncerramentoPropostaPncp"),
            "data_resultado": None,
            "numero_itens": None,
            "numero_processo": raw.get("processo", ""),
            "srp": raw.get("srp", False),
            "dados_brutos": raw,
        }

    def _parse_float(self, val):
        if val is None:
            return None
        try:
            return float(str(val).replace(",", "."))
        except (ValueError, TypeError):
            return None

    def _extract_date(self, dt_str):
        if not dt_str:
            return None
        return dt_str[:10] if len(dt_str) >= 10 else dt_str


class PNCPClient:
    """Cliente para API pncp.gov.br/api/consulta"""

    def __init__(self):
        self.base_url = BASE_URL_PNCP
        self.session = requests.Session()
        self.session.headers.update({"Accept": "application/json"})

    def buscar_contratacoes_por_publicacao(
        self,
        data_inicio: str,
        data_fim: str,
        pagina: int = 1,
        tam_pagina: int = 50
    ) -> list:
        """Busca contratações por data de publicação no PNCP."""
        try:
            resp = self.session.get(
                f"{self.base_url}/v1/contratacoes/publicacao",
                params={
                    "dataInicial": data_inicio,
                    "dataFinal": data_fim,
                    "pagina": pagina,
                    "tamanhoPagina": tam_pagina
                },
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"Erro API PNCP: {e}")
        return []

    def buscar_contratacoes_propostas_abertas(
        self,
        data_inicio: str,
        data_fim: str,
        pagina: int = 1
    ) -> list:
        """Busca contratações com propostas ainda abertas."""
        try:
            resp = self.session.get(
                f"{self.base_url}/v1/contratacoes/proposta",
                params={
                    "dataInicial": data_inicio,
                    "dataFinal": data_fim,
                    "pagina": pagina,
                    "tamanhoPagina": 50
                },
                timeout=30
            )
            if resp.status_code == 200:
                data = resp.json()
                return data if isinstance(data, list) else data.get("data", [])
        except Exception as e:
            print(f"Erro API PNCP propostas: {e}")
        return []

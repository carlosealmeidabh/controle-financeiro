from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional
from database import engine
from models import Base

Base.metadata.create_all(bind=engine)

app = FastAPI()

# modelo de dados
class Categoria(BaseModel):
    nome: str
    tipo_calculo: str  # normal / consignado
    margem_percentual: Optional[float] = Field(default=None)
    percentual_repasse: Optional[float] = Field(default=None)

class Compra(BaseModel):
    categoria_id: int
    valor: float

# banco temporário
categorias = []
compras = []

@app.get("/")
def home():
    return {"mensagem": "Sistema financeiro da banca rodando"}


@app.post("/categorias")
def criar_categoria(categoria: Categoria):

    tipo = categoria.tipo_calculo.strip().lower()
    margem = categoria.margem_percentual
    repasse = categoria.percentual_repasse

    # tratar 0 como None
    if margem == 0:
        margem = None
    if repasse == 0:
        repasse = None

    # validar tipo
    if tipo not in ["normal", "consignado", "markup"]:
        return {"erro": "tipo_calculo deve ser 'normal', 'consignado' ou 'markup'"}

    # validações + conversão
    if tipo == "normal":
        if margem is None or repasse is not None:
            return {"erro": "Categoria normal exige margem e não permite repasse"}

        if margem > 100:
            return {"erro": "margem_percentual deve ser menor que 100"}

        # 🔥 converte para decimal (padrão interno)
        margem = margem / 100

    elif tipo == "consignado":
        if margem is not None or repasse is None:
            return {"erro": "Categoria consignado exige repasse e não permite margem"}

        if repasse > 100:
            return {"erro": "percentual_repasse deve ser menor que 100"}

        # 🔥 converte para decimal
        repasse = repasse / 100

    elif tipo == "markup":
        if margem is None or repasse is not None:
            return {"erro": "Categoria markup exige margem e não permite repasse"}

        if margem < 0:
            return {"erro": "margem_percentual não pode ser negativa"}

        # converter para decimal
        margem = margem / 100

    nova = {
        "id": len(categorias) + 1,
        "nome": categoria.nome,
        "tipo_calculo": tipo,
        "margem_percentual": margem,
        "percentual_repasse": repasse
    }

    categorias.append(nova)
    return nova


@app.get("/categorias")
def listar_categorias():
    return categorias


@app.post("/compras")
def criar_compra(compra: Compra):

    # buscar categoria
    categoria = next((c for c in categorias if c["id"] == compra.categoria_id), None)

    if not categoria:
        return {"erro": "Categoria não encontrada"}

    custo = compra.valor

    # cálculo (agora padronizado)
    if categoria["tipo_calculo"] == "normal":
        margem = categoria["margem_percentual"]
        venda = custo / (1 - margem)

    elif categoria["tipo_calculo"] == "consignado":
        repasse = categoria["percentual_repasse"]
        venda = custo / repasse

    elif categoria["tipo_calculo"] == "markup":
        margem = categoria["margem_percentual"]
        venda = custo * (1 + margem)
        
    lucro = venda - custo

    nova = {
        "id": len(compras) + 1,
        "categoria_id": compra.categoria_id,
        "custo": custo,
        "venda_estimada": round(venda, 2),
        "lucro_estimado": round(lucro, 2)
    }

    compras.append(nova)
    return nova
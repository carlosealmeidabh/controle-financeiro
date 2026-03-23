from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Optional, Literal
from database import engine
from models import Base
from datetime import date
from enum import Enum

Base.metadata.create_all(bind=engine)

app = FastAPI()

# banco temporário (memória)
movimentacoes = []
fechamentos = []

# modelo de dados
class CategoriaEnum(str, Enum):
    compra = "compra"
    despesa = "despesa"
    retirada = "retirada"
    pagamento_conta = "pagamento_conta"
    transferencia = "transferência"


class FormaPagamentoEnum(str, Enum):
    dinheiro = "dinheiro"
    pix = "pix"
    banco = "banco"



class ContaEnum(str, Enum):
    caixa = "caixa"
    itau = "itau"
    infinitepay = "infinitepay"


class Movimentacao(BaseModel):
    tipo: Literal["entrada", "saida"] 
    categoria: CategoriaEnum
    forma_pagamento: FormaPagamentoEnum
    valor: float = Field(gt=0)
    data: date = Field(default_factory=date.today)   
    #data: Optional[date] = None
    conta: ContaEnum
    conta_destino: Optional[ContaEnum] = None

    descricao: Optional[str] = None
    origem: Optional[str] = None
    finalidade: Optional[str] = None

def obter_caixa_inicial(data):

    if not fechamentos:
        return 0  # primeiro dia

    # pega último fechamento
    ultimo = fechamentos[-1]

    return ultimo["caixa_real"]

class FechamentoDia(BaseModel):
    #data: Optional[date] = None
    data: date = Field(default_factory=date.today)
    # caixa_inicial: float vindo automaticamente agora
    caixa_final: float

    pix_itau: float
    pix_infinitepay: float
    debito_itau: float
    credito_itau: float
    voucher: float
    debito_infinitepay: float
    credito_infinitepay: float


@app.post("/movimentacoes")
def criar_movimentacao(mov: Movimentacao):

    # definir data automática se não vier
    if not mov.data:
       # mov.data = date.today()
        mov.data = Field(default_factory=date.today)

    # Atribui automaticamente saida ao tipo
    mov.tipo = "saida"

    # VALIDAÇÃO DE TRANSFERÊNCIA
    if mov.categoria == "transferencia":
        if not mov.conta_destino:
            return {"erro": "Transferência exige conta_destino"}

        if mov.conta_destino == mov.conta:
            return {"erro": "Conta origem e destino não podem ser iguais"}

    nova = mov.model_dump()

    movimentacoes.append(nova)

    return {
        "mensagem": "Movimentação registrada com sucesso",
        "dados": nova
    }

@app.get("/resumo")
def resumo():

    total_compras = sum(m["valor"] for m in movimentacoes if m["categoria"] == "compra")
    total_despesas = sum(m["valor"] for m in movimentacoes if m["categoria"] == "despesa")
    total_retiradas = sum(m["valor"] for m in movimentacoes if m["categoria"] == "retirada")
    total_transferencia = sum(m["valor"] for m in movimentacoes if m["categoria"] == "transferência")

    return {
        "compras": total_compras,
        "despesas": total_despesas,
        "retiradas": total_retiradas,
        "transferencia": total_transferencia
    }

@app.post("/fechamento")
def fechar_dia(dados: FechamentoDia):

    if not dados.data:
        dados.data = Field(default_factory=date.today)
        #date.today()
    caixa_inicial = obter_caixa_inicial(dados.data)    

    movs_do_dia = [
    m for m in movimentacoes
    if str(m["data"]) == str(dados.data)
    ]  


    compras = sum(m["valor"] for m in movs_do_dia if m["categoria"] == "compra")
    despesas = sum(m["valor"] for m in movs_do_dia if m["categoria"] == "despesa")
    retiradas = sum(m["valor"] for m in movs_do_dia if m["categoria"] == "retirada")

    transferencias = sum(m["valor"] for m in movs_do_dia if m["categoria"] == "transferencia")

    total_saidas = compras + despesas + retiradas   

    entradas_digitais = (
        dados.pix_itau +
        dados.pix_infinitepay +
        dados.debito_itau +
        dados.credito_itau +
        dados.debito_infinitepay +
        dados.credito_infinitepay +
        dados.voucher
    )
    movimento_caixa = dados.caixa_final - caixa_inicial

    entrada_dinheiro = movimento_caixa + total_saidas + transferencias

    venda_total = entrada_dinheiro + entradas_digitais

    caixa_esperado = caixa_inicial + entrada_dinheiro - total_saidas - transferencias

    diferenca = dados.caixa_final-caixa_esperado

    #lucro = venda - total_saidas

    return {

        "data": dados.data,

        "entrada_dinheiro": entrada_dinheiro,
        "entrada_digital": entradas_digitais,

        "venda_total": venda_total,

        "compras": compras,
        "despesas": despesas,
        "retiradas": retiradas,
        "transferencia": transferencias,

        "caixa esperado": caixa_esperado,
        "caixa_real": dados.caixa_final,
        "diferenca_caixa": diferenca
    }
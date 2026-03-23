from sqlalchemy import Column, Integer, String, Float
from database import Base

class Categoria(Base):
    __tablename__ = "categorias"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)
    tipo_calculo = Column(String)  # normal | consignado
    margem_percentual = Column(Float, nullable=True)
    percentual_repasse = Column(Float, nullable=True)
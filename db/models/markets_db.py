from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql.sqltypes import Integer, String, Boolean

from db.database import Base


class DbMarket(Base):
    __tablename__ = 'markets'
    id_market = Column('id_market', String, primary_key=True, index=True)
    id_user = Column('id_user', Integer, ForeignKey("users.id_user"))
    type_market = Column('type_market', String)
    web_page = Column('web_page', String)
    rfc = Column('rfc', String)
    dropped = Column('dropped', Boolean)

    branches = relationship(
        "db.models.branches_db.DbBranch",
        primaryjoin="and_(DbMarket.id_market==DbBranch.id_market, "
                    "DbBranch.dropped==False)",
        back_populates="market"
    )

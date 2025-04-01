from dataclasses import dataclass
from dao.base import BaseDAO
from dao.user_dao import UserDAO


# DAO namespace. List any BaseDAO derived here
@dataclass
class DAO:
    user: UserDAO
    
    @property
    def dao_list(self) -> list[BaseDAO]:
        return list(filter(lambda dao: isinstance(dao, BaseDAO), self.__dict__.values()))


async def setup_dao(app):
    app.Dao = DAO(
        user=UserDAO(app),
    )
    print(app.Dao.dao_list,'LIST DAO')
    for dao in app.Dao.dao_list:
        await dao.async_init()
from app.core.config import COLLECTION_USERS
from app.models.users import UserWithPasswordHash, UserInDb

from .crud_base import CRUDBase


class UserCRUD(CRUDBase[UserWithPasswordHash, UserInDb]):

    def __init__(self, collection_name: str):
        super().__init__(collection_name, UserWithPasswordHash, UserInDb)


UserCrudOp = UserCRUD(COLLECTION_USERS)

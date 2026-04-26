from app.core.config import COLLECTION_API_TOKENS, COLLECTION_USERS
from app.models.users import ApiToken, ApiTokenInDb, UserInDb, UserWithPasswordHash

from .crud_base import CRUDBase


class UserCRUD(CRUDBase[UserWithPasswordHash, UserInDb]):
    def __init__(self, collection_name: str):
        super().__init__(collection_name, UserWithPasswordHash, UserInDb)


class ApiTokenCRUD(CRUDBase[ApiToken, ApiTokenInDb]):
    def __init__(self, collection_name: str):
        super().__init__(collection_name, ApiToken, ApiTokenInDb)

    async def touch_last_used(self, db, by_id: str, when) -> None:
        import bson

        from .crud_base import get_collection

        await get_collection(db, self.collection).update_one(
            {'_id': bson.ObjectId(by_id)}, {'$set': {'last_used_at': when}}
        )


UserCrudOp = UserCRUD(COLLECTION_USERS)
ApiTokenCrudOp = ApiTokenCRUD(COLLECTION_API_TOKENS)

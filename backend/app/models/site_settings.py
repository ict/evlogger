from pydantic import BaseModel

from app.models.helpers import DbIdMixin


class SiteSettings(BaseModel):
    registration_enabled: bool = True


class SiteSettingsInDb(SiteSettings, DbIdMixin):
    pass

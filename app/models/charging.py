import datetime
from decimal import Decimal

from pydantic import BaseModel, Field
from pydantic_extra_types.color import Color


class Car(BaseModel):
    name: str
    make: str | None = None
    model: str | None = None
    color: Color = "black"


class DbIdMixin(BaseModel):
    id: str


class CarInDb(Car, DbIdMixin):
    pass


class CPO(BaseModel):
    name: str
    default_price: Decimal = Field(decimal_places=2, default="0.00")


class CPOInDb(CPO, DbIdMixin):
    pass


class Charge(BaseModel):
    date: datetime.datetime
    car_id: str
    car_name: str | None = None
    car_km: int
    kwh_charged: Decimal = Field(decimal_places=2)
    cpo_id: str
    cpo_name: str | None = None
    price_total: Decimal = Field(decimal_places=2)
    note: str | None = None


class ChargeInDb(Charge, DbIdMixin):
    pass

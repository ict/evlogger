import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field
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
    default_price: int = Field(..., description="Default price of one kWh in 1/100s of currency (e.g. cents)")


class CPOInDb(CPO, DbIdMixin):
    pass


class ChargeTypeEnum(str, Enum):
    ac = 'AC'
    dc = 'DC'


class Charge(BaseModel):
    date: datetime.datetime
    car_id: str
    car_name: str | None = None
    car_km: int
    kwh_charged: int | None = Field(..., description="Amount of kWh charged in 1/100s of a kWh")
    cpo_id: str
    cpo_name: str | None = None
    price_total: int | None = Field(description="Total amount paid in 1/100s of currency (e.g. cents)", default=None)
    charge_type: ChargeTypeEnum = Field(..., description="The type of charge, either AC (Wallbox, Wallplug) or DC")
    note: str | None = None

    @computed_field
    @property
    def price_per_kwh(self) -> int:
        return int(round(self.price_total / (self.kwh_charged / 100)))


class ChargeInDb(Charge, DbIdMixin):
    pass

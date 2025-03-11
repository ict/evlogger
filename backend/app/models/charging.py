import datetime
from enum import Enum

from pydantic import BaseModel, Field, computed_field, model_validator
from pydantic_extra_types.color import Color

from app.models.helpers import DbIdMixin


class Car(BaseModel):
    name: str
    make: str | None = None
    model: str | None = None
    color: Color = 'black'
    odometer: int = 0
    battery_capacity: int = Field(..., description='Battery capacity in kWh')


class CarInDb(Car, DbIdMixin):
    owner_id: str
    pass


class CPO(BaseModel):
    name: str
    default_price: int = Field(..., description='Default price of one kWh in 1/100s of currency (e.g. cents)')


class CPOInDb(CPO, DbIdMixin):
    owner_id: str
    pass


class ChargeTypeEnum(str, Enum):
    ac = 'AC'
    dc = 'DC'


class Charge(BaseModel):
    date: datetime.datetime
    car_id: str
    car_name: str | None = None
    car_odometer: int | None = None
    car_soc_after: int | None = Field(description='SoC of battery after charge', ge=0, le=100, default=None)
    kwh_charged: int = Field(..., description='Amount of kWh charged in 1/100s of a kWh')
    cpo_id: str
    cpo_name: str | None = None
    price_total: int | None = Field(description='Total amount paid in 1/100s of currency (e.g. cents)', default=None)
    charge_type: ChargeTypeEnum = Field(..., description='The type of charge, either AC (Wallbox, Wallplug) or DC')
    note: str | None = None

    @computed_field
    @property
    def price_per_kwh(self) -> int:
        if self.price_total is None:
            return 0
        return int(round(self.price_total / (self.kwh_charged / 100)))


class ChargeInDb(Charge, DbIdMixin):
    owner_id: str
    pass


class ChargeSubmission(Charge):
    car_km_driven: int | None = None

    @model_validator(mode='after')
    def validate_km(self):
        """One of the two values should be set"""
        if self.car_odometer is None and self.car_km_driven is None:
            msg = 'Either car_odometer or car_km_driven must be set'
            raise ValueError(msg)
        return self

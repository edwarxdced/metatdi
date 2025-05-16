from datetime import datetime

from pydantic import BaseModel

from enums.type_signals import TypeSignal


class TPTrail(BaseModel):
    trail_price: list[float]
    trail_time: list[datetime]


class SLTrail(BaseModel):
    trail_price: list[float]
    trail_time: list[datetime]


class Position(BaseModel):
    direction: TypeSignal
    entry_price: float
    exit_price: float
    pnl: float
    duration: float
    lot_size: float
    tp: float
    sl: float
    breakeven_applied: bool
    break_even_price: float
    tp_trail: TPTrail
    sl_trail: SLTrail
    tp_hit: bool
    sl_hit: bool
    entry_time: datetime
    exit_time: datetime
    is_closed: bool

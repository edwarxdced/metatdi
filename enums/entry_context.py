from enum import Enum


class EntryContext(Enum):
    BELOW_BOLLINGER = "below_bollinger"
    STANDARD = "standard"
    BAND_REJECTION = "band_rejection"

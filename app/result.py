class AddressTxInfo:
    address: str

    tx_count: int
    volume: float
    tx_fee: float
    active_days: int
    active_weeks: int
    active_monthes: int
    protocols: int
    first_day: str

    lite_tx_count: int
    lite_volume: float
    lite_days_start: int

    def __init__(self, **kwargs):
        for name, value in kwargs.items():
            setattr(self, name, value)

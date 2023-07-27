from typing import Any

from pydantic import BaseModel, Field, validator
from requests import Session

from app.config import logger
from app.info import LITE_TOKENS


def get_ether_price() -> float:
    url = "https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT"

    with Session() as session:
        data = session.get(url)
        data = data.json()
        return float(data["price"])


ETHER_PRICE = get_ether_price()


class LiteTransaction(BaseModel):
    # address: str
    timestamp: str = Field(alias="created_at")
    volume: Any = Field(alias="tx")

    @validator("timestamp")
    def get_timestamp(cls, value):
        return value[:10]

    @validator("volume")
    def sum_volume(cls, value):
        volume = 0
        tx_type = value.get("type")

        if tx_type == "Swap":
            if orders := value.get("orders"):
                for order in orders:
                    sell_token = order.get("tokenSell")
                    if token := LITE_TOKENS.get(sell_token):
                        amount = int(order.get("amount")) / 10 ** token["decimals"]
                        if sell_token == 0:
                            price = ETHER_PRICE
                        else:
                            price = 1
                        return amount * price

        elif tx_type in ["Transfer", "Deposit", "Withdraw"]:
            if tx_type == "Deposit":
                value = value["priority_op"]
            token = value["token"]
            amount = value["amount"]

            if token := LITE_TOKENS.get(token):
                amount = int(amount) / 10 ** token["decimals"]
                if token["symbol"] == "ETH":
                    price = ETHER_PRICE
                else:
                    price = 1
                return amount * price
        return volume


def get_all_lite_transactions(address: str) -> list[LiteTransaction]:
    url = "https://api.zksync.io/api/v0.1/account/{address}/history/{tx_counter}/100"
    tx_counter = 0
    tx_data = []
    with Session() as session:
        while True:
            try:
                resp = session.get(url.format(address=address, tx_counter=tx_counter))
                if resp.status_code == 200:
                    data = resp.json()

                    if len(data) == 0:
                        return tx_data

                    tx_data.extend(LiteTransaction.parse_obj(_) for _ in data)

                    if len(data) < 100:
                        return tx_data
                    tx_counter += 100
            except Exception as ex:
                logger.error(f"Error while parse Lite txs. {ex}")

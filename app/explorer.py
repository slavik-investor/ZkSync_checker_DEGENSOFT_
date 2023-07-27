from typing import Any, List, Optional

import requests
from pydantic import BaseModel, Field

from app.config import logger


class Token(BaseModel):
    price: Optional[float]
    balance: int
    contractAddress: str
    decimals: int
    name: str
    symbol: str
    type: str


class Transfer(BaseModel):
    from_address: str = Field(alias="from")
    to: str
    transactionHash: str
    timestamp: str
    amount: int | None
    tokenAddress: str
    type: str
    fields: Any
    token: dict | None

    def to_json(self):
        return self.__dict__


class Transaction(BaseModel):
    hash: str
    to: str
    from_address: str
    data: str
    isL1Originated: bool
    fee: str
    timestamp: str
    transfers: List[Transfer]
    ethValue: float


def get_token_list(address: str) -> List[Token]:
    try:
        response = requests.get(
            f"https://zksync2-mainnet.zkscan.io/api?module=account&action=tokenlist&address={address}"
        )
        return response.json()["result"]
    except Exception as e:
        logger.error(e)


def get_all_transfers(address: str) -> List[Transfer]:
    url = f"https://block-explorer-api.mainnet.zksync.io/address/{address}/transfers?limit=100&page=1"
    transfers = []

    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()["items"]
                transfers.extend(Transfer(**_) for _ in data)
                if response.json()["links"]["next"] == "":
                    break
                url = (
                    "https://block-explorer-api.mainnet.zksync.io/"
                    + response.json()["links"]["next"]
                )
            else:
                logger.error("Error occurred while retrieving transactions.")
                break
        except Exception as e:
            logger.error("Error occurred while making the request:", e)
            break

    return transfers


def assign_transfer_values(transactions: List[Transaction]):
    eth_response = requests.post(
        "https://mainnet.era.zksync.io/",
        json={
            "id": 42,
            "jsonrpc": "2.0",
            "method": "zks_getTokenPrice",
            "params": ["0x0000000000000000000000000000000000000000"],
        },
    )

    tokens_price = {
        "USDC": 1,
        "USDT": 1,
        "ZKUSD": 1,
        "CEBUSD": 1,
        "LUSD": 1,
        "ETH": float(eth_response.json()["result"]),
    }

    for transaction in transactions:
        for transfer in transaction.transfers:
            transfer.token["price"] = tokens_price.get(transfer.token["symbol"].upper())
        transaction.transfers = [
            transfer
            for transfer in transaction.transfers
            if transfer.token["price"] is not None
        ]


def get_transactions_list(address: str) -> List[Transaction]:
    url = f"https://block-explorer-api.mainnet.zksync.io/transactions?address={address}&limit=100&page=1"
    transactions = []

    eth_response = requests.post(
        "https://mainnet.era.zksync.io/",
        json={
            "id": 42,
            "jsonrpc": "2.0",
            "method": "zks_getTokenPrice",
            "params": ["0x0000000000000000000000000000000000000000"],
        },
    )

    while True:
        try:
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()["items"]
                for transaction_data in data:
                    transaction = Transaction(
                        hash=transaction_data["hash"],
                        to=transaction_data["to"],
                        from_address=transaction_data["from"],
                        data=transaction_data["data"],
                        isL1Originated=transaction_data["isL1Originated"],
                        fee=transaction_data["fee"],
                        timestamp=transaction_data["receivedAt"],
                        transfers=[],
                        ethValue=float(eth_response.json()["result"]),
                    )
                    transactions.append(transaction)

                if response.json()["links"]["next"] == "":
                    break
                url = (
                    "https://block-explorer-api.mainnet.zksync.io/"
                    + response.json()["links"]["next"]
                )
            else:
                logger.error("Error occurred while retrieving transactions.")
                print(response.text)
                break
        except Exception as e:
            logger.error("Error occurred while making the request:", e)
            break

    transfers = get_all_transfers(address)

    for transfer in transfers:
        if transfer.token is None:
            continue
        for transaction in transactions:
            if transaction.hash == transfer.transactionHash:
                transaction.transfers.append(transfer)

    assign_transfer_values(transactions)

    return transactions

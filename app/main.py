import datetime

import pandas as pd

from app.config import logger
from app.explorer import Transaction, get_transactions_list
from app.info import PROTOCOLS
from app.lite_explorer import get_all_lite_transactions
from app.result import AddressTxInfo


def activity_summary(dates):
    # Преобразование списка дат в формат datetime и создание DataFrame
    df = pd.DataFrame(dates, columns=["Date"])
    df.dropna()
    df["Date"] = pd.to_datetime(df["Date"])

    # Подсчет активных дней, недель, месяцев
    active_days = df["Date"].nunique()
    active_weeks = df["Date"].dt.isocalendar().week.nunique()
    active_months = df["Date"].dt.to_period("M").nunique()

    # Поиск первого дня активности
    first_day = df["Date"].min().strftime("%Y-%m-%d")

    return active_days, active_weeks, active_months, first_day


def find_protocol(address: str) -> str | None:
    for key, addresses in PROTOCOLS.items():
        if address in addresses:
            return key


def get_volume_of_tx(txs: Transaction, from_address: str) -> float:
    volume = 0
    for transfer in txs.transfers:
        if transfer.from_address.lower() != from_address:
            continue
        if transfer.token and transfer.amount:
            volume += (
                transfer.amount
                / 10 ** transfer.token["decimals"]
                * transfer.token["price"]
            )
    return volume


def get_address_stat(txs: list[Transaction], address: str) -> AddressTxInfo:
    address = address.lower()
    protocols_dict_useage = {key: 0 for key in PROTOCOLS.keys()}
    activity_days = set()
    fee = 0
    volume = 0

    for tx in txs:
        volume += get_volume_of_tx(tx, address)

        # protocols
        for transfer in tx.transfers:
            to_protocol = find_protocol(transfer.to.lower())
            from_protocol = find_protocol(transfer.from_address.lower())
            protocol = from_protocol if from_protocol else to_protocol
            if protocol:
                protocols_dict_useage[protocol] += 1
        to_protocol = find_protocol(tx.to.lower())
        from_protocol = find_protocol(tx.from_address.lower())
        protocol = from_protocol if from_protocol else to_protocol
        if protocol:
            protocols_dict_useage[protocol] += 1

        # fee
        if tx.from_address.lower() == address:
            fee += int(tx.fee, 16)

        # activity days
        activity_days.add(tx.timestamp[:11])

    unique_protocols = [key for key, value in protocols_dict_useage.items() if value]
    fee = round(fee / 10**18, 6)
    volume = round(volume, 3)
    activ_days, activ_weeks, activ_month, first_day = activity_summary(activity_days)

    return AddressTxInfo(
        address=address,
        tx_count=len(txs),
        volume=volume,
        tx_fee=fee,
        activ_days=activ_days,
        activ_weeks=activ_weeks,
        activ_month=activ_month,
        protocols=len(unique_protocols),
        first_day=first_day,
    )


def get_zk_era_info(address: str):
    txs = get_transactions_list(address)
    if len(txs) == 0:
        return AddressTxInfo(
            address=address,
            tx_count=0,
            volume=0,
            tx_fee=0,
            activ_days=0,
            activ_weeks=0,
            activ_month=0,
            protocols=0,
            first_day=0,
        ).__dict__
    return get_address_stat(txs, address).__dict__


def get_zk_lite_info(address: str):
    txs = get_all_lite_transactions(address)
    if len(txs) == 0:
        return 0, 0, 0
    volume = sum(tx.volume for tx in txs)
    volume = round(volume, 3)
    _, _, _, first_day = activity_summary(tx.timestamp for tx in txs)
    tx_count = len(txs)
    days_after_start = (
        datetime.date.today() - datetime.date.fromisoformat(first_day)
    ).days
    return tx_count, volume, days_after_start


def main():
    ascii = '''              
                             ██████╗░███████╗░██████╗░███████╗███╗░░██╗░██████╗░█████╗░███████╗████████╗
                             ██╔══██╗██╔════╝██╔════╝░██╔════╝████╗░██║██╔════╝██╔══██╗██╔════╝╚══██╔══╝
                             ██║░░██║█████╗░░██║░░██╗░█████╗░░██╔██╗██║╚█████╗░██║░░██║█████╗░░░░░██║░░░
                             ██║░░██║██╔══╝░░██║░░╚██╗██╔══╝░░██║╚████║░╚═══██╗██║░░██║██╔══╝░░░░░██║░░░
                             ██████╔╝███████╗╚██████╔╝███████╗██║░╚███║██████╔╝╚█████╔╝██║░░░░░░░░██║░░░
                             ╚═════╝░╚══════╝░╚═════╝░╚══════╝╚═╝░░╚══╝╚═════╝░░╚════╝░╚═╝░░░░░░░░╚═╝░░░

 ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄ ▄▄



                  █░█ ▀█▀ ▀█▀ █▀█ █▀ ▀ ░░▄▀ ░░▄▀ ▀█▀ ░ █▀▄▀█ █▀▀ ░░▄▀ █▀▄ █▀▀ █▀▀ █▀▀ █▄░█ █▀ █▀█ █▀▀ ▀█▀ █▄▄ █▀█ ▀█▀
                  █▀█ ░█░ ░█░ █▀▀ ▄█ ▄ ▄▀░░ ▄▀░░ ░█░ ▄ █░▀░█ ██▄ ▄▀░░ █▄▀ ██▄ █▄█ ██▄ █░▀█ ▄█ █▄█ █▀░ ░█░ █▄█ █▄█ ░█░

                           Degensoft c 2023 AUTOMATIZATION OF FARMING AIRDROPS | https://t.me/DegenSoftBot
                           
                           '''
   
    print(ascii)
    with open("wallets.txt", "r") as file:
        addresses = [line.strip().lower() for line in file.readlines()]

    data = []
    for i, address in enumerate(addresses, 1):
        logger.info(f"{address} ({i}/{len(addresses)})")
        info = get_zk_era_info(address)
        lite_tx_count, lite_volume_usd, lite_days = get_zk_lite_info(address)
        info["lite_tx_count"] = lite_tx_count
        info["lite_volume_usd"] = lite_volume_usd
        info["lite_days_start"] = lite_days
        if info:
            data.append(info)

    logger.info("Generate excel file")
    df = pd.DataFrame(data)
    df.to_excel("result.xlsx")
    logger.success("All done")

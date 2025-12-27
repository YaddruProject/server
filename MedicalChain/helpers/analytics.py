import time

from MedicalChain.config import Config
from MedicalChain.models import Analytics

web3, contract = Config.setupWeb3()
sender_address = web3.eth.account.from_key(Config.PRIVATE_KEY).address


def send_signed_transaction():
    nonce = web3.eth.get_transaction_count(sender_address)
    tx = contract.functions.sendTransaction().build_transaction(
        {
            "from": sender_address,
            "gas": 200000,
            "gasPrice": web3.to_wei("5", "gwei"),
            "nonce": nonce,
        },
    )
    signed_tx = web3.eth.account.sign_transaction(tx, Config.PRIVATE_KEY)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
    web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_hash


def calculate_throughput():
    try:
        number_of_transactions = 5
        start_time = time.time()
        for _ in range(number_of_transactions):
            send_signed_transaction()
        end_time = time.time()
        duration_seconds = end_time - start_time
        throughput = number_of_transactions / duration_seconds
        if len(Config.THROUGHPUT) == 5:
            Config.THROUGHPUT.pop(0)
        Config.THROUGHPUT.append(Analytics(value=round(throughput, 4)))
    except Exception as e:
        raise Exception(str(e))


def measure_latency():
    try:
        start_time = time.time()
        send_signed_transaction()
        end_time = time.time()
        latency = (end_time - start_time) * 1000
        if len(Config.LATENCY) == 5:
            Config.LATENCY.pop(0)
        Config.LATENCY.append(Analytics(value=round(latency, 4)))
    except Exception as e:
        raise Exception(str(e))

from typing import List, Tuple

from dotenv import load_dotenv
from MedicalChain.models import Analytics
from NoobStuffs.libenvconfig import getConfig
from web3.contract import Contract

from web3 import Web3

load_dotenv("config.env")


class Config:
    PRIVATE_KEY: str = getConfig("PRIVATE_KEY", True)
    NETWORK_PROVIDER: str = getConfig("NETWORK_PROVIDER", True)
    CONTRACT_ABI: str = getConfig("CONTRACT_ABI", True)
    CONTRACT_ADDRESS: str = getConfig("CONTRACT_ADDRESS", True)

    GROQ_API_KEY: str = getConfig("GROQ_API_KEY", True)

    THROUGHPUT: List[Analytics] = []
    LATENCY: List[Analytics] = []
    ENCRYPTION: List[Analytics] = []
    DECRYPTION: List[Analytics] = []

    @classmethod
    def setupWeb3(cls) -> Tuple[Web3, Contract]:
        web3 = Web3(
            Web3.HTTPProvider(cls.NETWORK_PROVIDER, request_kwargs={"timeout": 60}),
        )
        if not web3.is_connected():
            raise Exception("Failed to connect to the Ethereum network")
        contract = web3.eth.contract(address=cls.CONTRACT_ADDRESS, abi=cls.CONTRACT_ABI)
        return web3, contract

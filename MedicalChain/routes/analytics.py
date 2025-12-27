from typing import List

from fastapi import APIRouter, HTTPException
from MedicalChain.config import Config
from MedicalChain.models import Analytics

router = APIRouter(prefix="/analytics", tags=["analytics"])

web3, contract = Config.setupWeb3()


@router.get("/throughput", response_model=List[Analytics])
async def measure_throughput():
    try:
        return Config.THROUGHPUT
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/latency", response_model=List[Analytics])
async def measure_latency():
    try:
        return Config.LATENCY
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/encryption", response_model=List[Analytics])
async def measure_encryption():
    try:
        return Config.ENCRYPTION
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/decryption", response_model=List[Analytics])
async def measure_decryption():
    try:
        return Config.DECRYPTION
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/encryption")
async def update_encryption(time: float):
    try:
        if len(Config.ENCRYPTION) == 5:
            Config.ENCRYPTION.pop(0)
        Config.ENCRYPTION.append(Analytics(value=time))
        return {"message": "Encryption time updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/decryption")
async def update_decryption(time: float):
    try:
        if len(Config.DECRYPTION) == 5:
            Config.DECRYPTION.pop(0)
        Config.DECRYPTION.append(Analytics(value=time))
        return {"message": "Decryption time updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

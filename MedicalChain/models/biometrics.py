from pydantic import BaseModel

class Biometrics(BaseModel):
    verified: bool
    confidence: float
    time: float

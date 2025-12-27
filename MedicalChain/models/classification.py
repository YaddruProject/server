from pydantic import BaseModel


class CodeResponse(BaseModel):
    code: int
    name: str
    confidence: float

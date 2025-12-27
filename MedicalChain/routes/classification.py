from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from MedicalChain.helpers.classifier import (
    classify_medical_file,
    classify_specialization,
    determine_related_access_codes,
)
from MedicalChain.helpers.hierarchy import hierarchy_helper
from MedicalChain.models import (
    CodeResponse,
)

router = APIRouter(prefix="/classification", tags=["classification"])


@router.post("/get-code", response_model=CodeResponse)
async def get_specialization_code(specialization: str = Form(...)):
    try:
        result = classify_specialization(specialization)
        return CodeResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not classify specialization: {str(e)}",
        )


@router.post("/classify-file", response_model=CodeResponse)
async def classify_file(
    file: UploadFile = File(...),
    description: str = Form(...),
):
    try:
        result = await classify_medical_file(
            file,
            description,
        )
        return CodeResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not classify file: {str(e)}",
        )


@router.get("/specializations")
async def get_all_specializations():
    return {
        "specializations": hierarchy_helper.get_all_specializations(),
        "count": len(hierarchy_helper.get_all_codes()),
    }


@router.get("/code/{code}")
async def get_code_details(code: int):
    name = hierarchy_helper.get_name_by_code(code)
    if name == "Unknown":
        raise HTTPException(status_code=404, detail="Code not found")
    return {
        "code": code,
        "name": name,
        "category": code // 1000,
        "specialty": (code // 100) % 100,
    }


@router.post("/determine-access")
async def determine_access(
    specializationCode: int = Form(...),
):
    """
    LLM determines what related codes a doctor needs access to based on their specialization
    """
    try:
        codes = determine_related_access_codes(specializationCode)
        return {
            "codes": codes,
            "primary_code": specializationCode,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Could not determine access codes: {str(e)}",
        )

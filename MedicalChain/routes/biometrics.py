import os

from fastapi import APIRouter, HTTPException, UploadFile
from MedicalChain.helpers.deepface import verify_faces
from MedicalChain.models import Biometrics

router = APIRouter(prefix="/biometrics", tags=["biometrics"])


@router.post("/verify", response_model=Biometrics)
async def verify_face(img1: UploadFile, img2: UploadFile):
    img1_path = None
    img2_path = None
    try:
        allowed_types = ["image/jpeg", "image/jpg", "image/png"]
        if (
            img1.content_type not in allowed_types
            or img2.content_type not in allowed_types
        ):
            raise HTTPException(
                status_code=400,
                detail="Only JPEG and PNG images are allowed",
            )
        img1_path = f"temp_{img1.filename}"
        img2_path = f"temp_{img2.filename}"
        with open(img1_path, "wb") as f:
            f.write(await img1.read())
        with open(img2_path, "wb") as f:
            f.write(await img2.read())
        result = verify_faces(img1_path, img2_path)
        return Biometrics(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Face verification failed: {str(e)}",
        )
    finally:
        if img1_path and os.path.exists(img1_path):
            os.remove(img1_path)
        if img2_path and os.path.exists(img2_path):
            os.remove(img2_path)

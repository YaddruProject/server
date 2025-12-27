from deepface import DeepFace

def verify_faces(img1_path: str, img2_path: str):
    try:
        result = DeepFace.verify(img1_path, img2_path)
        return result
    except Exception as e:
        raise Exception(str(e))

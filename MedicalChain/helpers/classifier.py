import base64
import io
import json

from docx import Document
from groq import Groq
from MedicalChain.config import Config
from MedicalChain.helpers.hierarchy import hierarchy_helper
from PyPDF2 import PdfReader

client = Groq(api_key=Config.GROQ_API_KEY)


def _determine_category(specialization: str, hierarchy) -> tuple:
    """
    Use LLM to determine which category and specialty a new specialization belongs to
    Returns: (category_id, specialty_id, base_code)
    """
    # Build hierarchy structure for LLM
    hierarchy_info = []
    for cat_id, cat_data in hierarchy.items():
        cat_name = cat_data.get("name", "")
        specialties = cat_data.get("specialties", {})
        for spec_id, spec_data in specialties.items():
            spec_name = spec_data.get("name", "")
            codes = spec_data.get("codes", {})
            base_code = int(list(codes.keys())[0]) if codes else 0
            hierarchy_info.append(
                f"Category {cat_id} ({cat_name}) -> Specialty {spec_id} ({spec_name}) -> Base Code: {base_code}",
            )

    hierarchy_text = "\n".join(hierarchy_info)

    prompt = f"""You are a medical classification expert. Analyze this new specialization and determine where it belongs in the hierarchy.

New Specialization: "{specialization}"

Existing Hierarchy:
{hierarchy_text}

Analyze the specialization and determine:
1. Which CATEGORY it belongs to (Create a new category if needed)
2. Which SPECIALTY within that category it belongs to (Create a new specialty if needed)
3. The base code for that specialty

Return ONLY a JSON object:
{{
  "category_id": "1",
  "specialty_id": "12",
  "base_code": 1200,
  "reasoning": "brief explanation"
}}
"""

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical classification expert. Return ONLY valid JSON with no additional text or explanations outside the JSON object.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_completion_tokens=300,
        )

        response_content = completion.choices[0].message.content.strip()
        if response_content.startswith("```"):
            response_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )

        result = json.loads(response_content)
        return (
            str(result.get("category_id", "9")),
            str(result.get("specialty_id", "91")),
            int(result.get("base_code", 9100)),
        )
    except Exception as e:
        print(f"LLM category determination failed: {e}, using code 0 fallback")
        # Ultimate fallback - code 0 (All Specializations)
        return ("0", "0", 0)


def classify_specialization(specialization: str) -> dict:
    """
    Use LLM to find hierarchical code for doctor's specialization

    Args:
        specialization: Doctor's specialization as string

    Returns:
        dict with code, name, confidence
    """
    # Get all available specializations
    all_specs = hierarchy_helper.get_all_specializations()

    # Create prompt for LLM
    spec_list = "\n".join([f"{s['code']}: {s['name']}" for s in all_specs])

    prompt = f"""You are a medical classification expert. Find the BEST matching code for this specialization.

Available codes:
{spec_list}

User's specialization: "{specialization}"

CRITICAL RULES:
1. You MUST return a code that EXISTS in the available codes list above
2. If input is GENERAL or VAGUE, return the BASE/GENERAL code (codes ending in 00)
3. If input is SPECIFIC, return the specific code
4. Look for KEYWORDS to determine category:
   - "surgery/surgical/cut/operation/transplant" → Surgery categories (2xxx) OR specific surgical codes
   - "medicine/physician/doctor" → Medicine categories (1xxx, 4xxx, etc.)
5. BASE codes usually end in 00 (1200, 2100, 3100, 4100)
6. NEVER make up or invent new codes
7. DO NOT write explanations or text outside the JSON
8. Return ONLY a valid JSON object with no additional text before or after

Return ONLY this JSON format (no other text):
{{
  "code": 1234,
  "reasoning": "brief explanation",
  "confidence": 0.95
}}
"""

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical classification expert. Return ONLY valid JSON with no additional text or explanations outside the JSON object.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_completion_tokens=500,
        )

        response_content = completion.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_content.startswith("```"):
            response_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )

        # Try to extract JSON from response if LLM added extra text
        import re

        json_match = re.search(r"\{[^}]+\}", response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group(0)

        result = json.loads(response_content)
        code = int(result.get("code", 0))

        # Check if code exists in hierarchy
        if code in hierarchy_helper.get_all_codes():
            return {
                "code": code,
                "name": hierarchy_helper.get_name_by_code(code),
                "confidence": float(result.get("confidence", 0.8)),
            }

        # LLM returned a code that doesn't exist - create it dynamically
        print(f"LLM returned code {code} which doesn't exist. Creating dynamically...")

    except Exception as e:
        print(f"LLM API call failed: {str(e)}, proceeding to dynamic creation...")

        # Dynamic classification: Create new specialization
        print(f"Creating new specialization for '{specialization}'...")

        # Use LLM to determine category and specialty
        category_id, specialty_id, base_code = _determine_category(
            specialization,
            hierarchy_helper.hierarchy,
        )

        # Check if category determination failed (returned code 0)
        if base_code == 0:
            print(
                f"Category determination failed for '{specialization}', returning code 0",
            )
            return {
                "code": 0,
                "name": "All Specializations (General Access)",
                "confidence": 0.1,
            }

        # Find next available code in this specialty group
        existing_codes = [
            c for c in hierarchy_helper.get_all_codes() if c // 100 == base_code // 100
        ]
        if existing_codes:
            new_code = max(existing_codes) + 1
        else:
            new_code = base_code + 1

        # Add to hierarchy
        success = hierarchy_helper.add_specialization(
            code=new_code,
            name=specialization.title(),
            category_id=category_id,
            specialty_id=specialty_id,
        )

        if success:
            print(f"Created new specialization: {new_code} - {specialization.title()}")
            return {
                "code": new_code,
                "name": specialization.title(),
                "confidence": 0.5,
            }
        else:
            # Ultimate fallback - code 0 (All Specializations)
            print(f"Dynamic creation failed for '{specialization}', returning code 0")
            return {
                "code": 0,
                "name": "All Specializations (General Access)",
                "confidence": 0.1,
            }


def determine_related_access_codes(specialization_code: int) -> list:
    """
    Use LLM to determine which related codes a doctor needs access to based on their specialization

    Args:
        specialization_code: Doctor's primary specialization code

    Returns:
        list of codes the doctor should have access to
    """
    spec_name = hierarchy_helper.get_name_by_code(specialization_code)
    if spec_name == "Unknown":
        return [specialization_code]

    all_specs = hierarchy_helper.get_all_specializations()
    spec_list = "\n".join([f"{s['code']}: {s['name']}" for s in all_specs])

    prompt = f"""You are a medical access control expert determining which DIAGNOSTIC and SUPPORT service codes a doctor needs.

Doctor's specialization: {spec_name} (Code: {specialization_code})

Available codes:
{spec_list}

CRITICAL DECISION FRAMEWORK:

Does this specialty ORDER or INTERPRET diagnostic tests as part of their PRIMARY clinical workflow?

If NO (e.g., Psychiatry, Counseling, Palliative Care) → Return ONLY the primary code [{specialization_code}]
If YES → Include relevant diagnostic codes from category 6xxx

DIAGNOSTIC CODES (6xxx):
- 6100: Radiology (X-ray, CT, MRI)
- 6200: Pathology (tissue/biopsy analysis)
- 6300: Lab Medicine (blood tests, cultures)

STRICT RULES:
1. ALWAYS include primary code ({specialization_code})
2. ONLY add codes from 6xxx category if the doctor orders/reviews those tests regularly
3. Psychiatrists DO NOT need any 6xxx codes - they work through clinical interviews, not lab/imaging
4. DO NOT add other clinical specialty codes (1xxx-5xxx, 7xxx-9xxx)
5. Return codes that EXIST in the list above
6. Return ONLY valid JSON with no additional text

Return ONLY this JSON format:
{{
  "codes": [4200],
  "reasoning": "brief explanation"
}}
"""

    try:
        completion = client.chat.completions.create(
            model="meta-llama/llama-4-scout-17b-16e-instruct",
            messages=[
                {
                    "role": "system",
                    "content": "You are a medical access control expert. Return ONLY valid JSON with no additional text or explanations outside the JSON object.",
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            temperature=0.1,
            max_completion_tokens=500,
        )

        response_content = completion.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_content.startswith("```"):
            response_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )

        # Try to extract JSON from response if LLM added extra text
        import re

        json_match = re.search(r"\{[^}]+\}", response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group(0)

        result = json.loads(response_content)
        codes = result.get("codes", [])

        # Validate all codes exist
        valid_codes = [
            c for c in codes if c in hierarchy_helper.get_all_codes() or c == 0
        ]

        # Ensure primary code is included
        if specialization_code not in valid_codes and specialization_code != 0:
            valid_codes.append(specialization_code)

        print(
            f"Related access codes for {spec_name} ({specialization_code}): {valid_codes}",
        )

        return valid_codes

    except Exception as e:
        print(f"LLM access determination failed: {str(e)}, returning primary code only")
        # Fallback: just return primary code
        return [specialization_code]


async def classify_medical_file(
    file,
    description: str,
) -> dict:
    """
    Use LLM to classify medical file and return hierarchical code
    Supports images (sent directly to vision model), text, PDFs, and documents

    Args:
        file: UploadFile object from FastAPI
        description: File description

    Returns:
        dict with code, name, confidence
    """
    filename = file.filename
    file_type = file.content_type

    # Determine if this is an image file that supports vision
    is_image = (
        file_type and file_type.startswith("image/")
        if file_type
        else filename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".webp"))
    )

    # Read file content based on type
    max_size = 10_000_000 if is_image else 5_000_000  # 10MB for images, 5MB for others

    file_content = None
    if file.size and file.size < max_size:
        file_content = await file.read()
        await file.seek(0)  # Reset file pointer for potential reuse

    # Get all available specializations
    all_specs = hierarchy_helper.get_all_specializations()
    spec_list = "\n".join([f"{s['code']}: {s['name']}" for s in all_specs])

    # Prepare content for LLM
    content_preview = ""
    messages = []

    if is_image and file_content:
        # For images, use vision-capable model with base64 encoding
        base64_image = base64.b64encode(file_content).decode("utf-8")

        messages = [
            {
                "role": "system",
                "content": "You are a medical imaging classification expert. Analyze medical images and classify them into the correct medical specialization. Return ONLY valid JSON with no additional text or explanations outside the JSON object.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""Analyze this medical image and classify it.

Available specialization codes:
{spec_list}

Filename: {filename}
Description: {description}

CRITICAL RULES:
1. You MUST return a code that EXISTS in the available codes list above
2. Analyze the image content, filename, and description
3. Return the MOST SPECIFIC code that applies
4. Look for visual indicators to determine if it's surgical, diagnostic, or clinical
5. NEVER make up or invent new codes
6. DO NOT write explanations or text outside the JSON
7. Return ONLY a valid JSON object with no additional text before or after

Return ONLY this JSON format (no other text):
{{
  "code": 1234,
  "reasoning": "brief explanation of what you see and why this code applies",
  "confidence": 0.95
}}
""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{file_type or 'image/jpeg'};base64,{base64_image}",
                        },
                    },
                ],
            },
        ]
        model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Vision-capable model

    else:
        # For text, PDFs, documents - extract complete text content
        content_preview = ""
        if file_content:
            try:
                # Extract text based on file type
                if filename.lower().endswith(".pdf"):
                    # Extract all text from PDF
                    pdf_reader = PdfReader(io.BytesIO(file_content))
                    all_text = []
                    for page in pdf_reader.pages:
                        page_text = page.extract_text()
                        if page_text:
                            all_text.append(page_text)
                    content_preview = "\n\n".join(all_text)

                elif filename.lower().endswith((".doc", ".docx")):
                    # Extract all text from Word document
                    doc = Document(io.BytesIO(file_content))
                    all_paragraphs = [
                        para.text for para in doc.paragraphs if para.text.strip()
                    ]
                    content_preview = "\n".join(all_paragraphs)

                else:
                    # Try to decode as plain text
                    content_preview = file_content.decode("utf-8", errors="ignore")

            except Exception as e:
                print(f"Text extraction failed: {e}")
                content_preview = "Content extraction failed - analyzing filename and description only"

        prompt = f"""You are a medical records classification expert. Classify this medical file.

Available codes:
{spec_list}

Medical File:
- Filename: {filename}
- File Type: {file_type or 'unknown'}
- Description: {description}
{f"- Content preview: {content_preview}" if content_preview else "- No content preview available"}

CRITICAL RULES:
1. You MUST return a code that EXISTS in the available codes list above
2. Return the MOST SPECIFIC code that applies
3. Consider filename, file type, description, and content
4. Look for KEYWORDS to determine category:
   - "surgery/surgical/operation/post-op/pre-op" → Surgery categories (2xxx)
   - "lab/blood/test/results" → Lab Medicine (63xx)
   - "imaging/x-ray/scan/MRI/CT" → Radiology (61xx)
   - "pathology/biopsy/histology" → Pathology (62xx)
5. NEVER make up or invent new codes
6. DO NOT write explanations or text outside the JSON
7. Return ONLY a valid JSON object with no additional text before or after

Return ONLY this JSON format (no other text):
{{
  "code": 1234,
  "reasoning": "brief explanation",
  "confidence": 0.95
}}
"""

        messages = [
            {
                "role": "system",
                "content": "You are a medical classification expert. Return ONLY valid JSON with no additional text or explanations outside the JSON object.",
            },
            {
                "role": "user",
                "content": prompt,
            },
        ]
        model = "meta-llama/llama-4-scout-17b-16e-instruct"  # Text model

    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.1,
            max_completion_tokens=500,
        )

        response_content = completion.choices[0].message.content.strip()

        # Remove markdown code blocks if present
        if response_content.startswith("```"):
            response_content = (
                response_content.replace("```json", "").replace("```", "").strip()
            )

        # Try to extract JSON from response if LLM added extra text
        import re

        json_match = re.search(r"\{[^}]+\}", response_content, re.DOTALL)
        if json_match:
            response_content = json_match.group(0)

        result = json.loads(response_content)
        code = int(result.get("code", 0))

        if code not in hierarchy_helper.get_all_codes():
            # Try to find closest match
            code = hierarchy_helper.get_code_by_name(filename)
            if not code:
                code = 0  # All Specializations fallback

        return {
            "code": code,
            "name": (
                hierarchy_helper.get_name_by_code(code)
                if code != 0
                else "All Specializations (General Access)"
            ),
            "confidence": float(result.get("confidence", 0.8)) if code != 0 else 0.1,
        }

    except Exception as e:
        print(f"LLM classification failed: {str(e)}")
        # Ultimate fallback - code 0 (All Specializations)
        return {
            "code": 0,
            "name": "All Specializations (General Access)",
            "confidence": 0.1,
        }

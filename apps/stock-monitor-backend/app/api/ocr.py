"""
OCR and Vision API
Handles image text recognition and analysis
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Optional
import base64
import io

router = APIRouter(prefix="/api/ocr", tags=["ocr"])


@router.post("/")
async def perform_ocr(
    image: UploadFile = File(...),
    language: Optional[str] = "chi_sim+eng"
):
    """Perform OCR on an image"""
    try:
        # Read image data
        image_data = await image.read()
        
        # Try to use pytesseract if available
        try:
            import pytesseract
            from PIL import Image
            
            # Convert to PIL Image
            img = Image.open(io.BytesIO(image_data))
            
            # Perform OCR
            text = pytesseract.image_to_string(img, lang=language)
            
            return {
                "success": True,
                "text": text.strip(),
                "language": language
            }
        except ImportError:
            # Fallback: return base64 for manual processing
            return {
                "success": True,
                "text": "",
                "base64": base64.b64encode(image_data).decode('utf-8'),
                "message": "OCR service not configured. Image returned as base64."
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze")
async def analyze_image(
    image: UploadFile = File(...),
    prompt: Optional[str] = "描述这张图片"
):
    """Analyze image using vision model"""
    try:
        # Read image data
        image_data = await image.read()
        base64_image = base64.b64encode(image_data).decode('utf-8')
        
        # Try to use OpenAI or other vision API if configured
        try:
            import openai
            import os
            
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                client = openai.OpenAI(api_key=api_key)
                
                response = client.chat.completions.create(
                    model="gpt-4-vision-preview",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {"type": "text", "text": prompt},
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/jpeg;base64,{base64_image}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=1000
                )
                
                return {
                    "success": True,
                    "analysis": response.choices[0].message.content,
                    "model": "gpt-4-vision-preview"
                }
        except Exception as e:
            print(f"Vision API error: {e}")
        
        # Fallback response
        return {
            "success": True,
            "analysis": "Vision analysis not available. Image processed but no AI analysis performed.",
            "base64": base64_image[:100] + "...",  # Truncated for response
            "prompt": prompt
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/extract-text")
async def extract_text_regions(
    image: UploadFile = File(...)
):
    """Extract text regions from image"""
    try:
        image_data = await image.read()
        
        try:
            import pytesseract
            from PIL import Image
            
            img = Image.open(io.BytesIO(image_data))
            
            # Get detailed OCR data with bounding boxes
            data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
            
            regions = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 30:  # Confidence threshold
                    regions.append({
                        "text": data['text'][i],
                        "confidence": data['conf'][i],
                        "bbox": {
                            "x": data['left'][i],
                            "y": data['top'][i],
                            "width": data['width'][i],
                            "height": data['height'][i]
                        }
                    })
            
            return {
                "success": True,
                "regions": regions,
                "total_regions": len(regions)
            }
        except ImportError:
            return {
                "success": False,
                "error": "OCR libraries not installed",
                "regions": []
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

import os
import logging
import google.generativeai as genai
from .dict import return_disease, show, get_dict

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if api_key:
    genai.configure(api_key=api_key)

def predict_image_class(image_path):
    if not api_key:
        return {"error": "GEMINI_API_KEY is missing from environment variables."}
        
    try:
        import PIL.Image
        img = PIL.Image.open(image_path)
        
        # Use gemini-1.5-flash (Requires google-generativeai>=0.7.2)
        model = genai.GenerativeModel("gemini-pro-vision")
        
        prompt = """
        You are an expert agricultural AI. 
        Analyze this plant leaf image. Is it healthy or does it have a disease?
        You MUST respond with exactly one of the following exact strings and nothing else:
        - "Downey Mildew"
        - "Pepper__bell___Bacterial_spot"
        - "Tomato__Tomato_YellowLeaf__Curl_Virus"
        - "Tomato__Tomato_mosaic_virus"
        - "healthy"
        
        If it is a healthy tomato or pepper leaf, respond with "healthy".
        If it does not clearly match one of these, make your best guess among these options.
        Do not include any other text, markdown, or punctuation.
        """
        
        response = model.generate_content([prompt, img])
        result = response.text.strip().replace("\"", "").replace("`", "")
        
        logging.info(f"Gemini predicted: {result}")
        
        if "healthy" in result.lower():
            return "healthy"
            
        # Try to match the exact string to our dict
        valid_keys = [
            "Downey Mildew", 
            "Pepper__bell___Bacterial_spot", 
            "Tomato__Tomato_YellowLeaf__Curl_Virus", 
            "Tomato__Tomato_mosaic_virus"
        ]
        
        if result in valid_keys:
            return get_dict(result)
            
        # Fallback if it slightly hallucinates the string
        for key in valid_keys:
            if key.lower() in result.lower() or result.lower() in key.lower():
                return get_dict(key)
                
        return {"error": f"Model could not confidently classify the disease. It said: {result}"}
        
    except Exception as e:
        logging.error(f"Gemini prediction failed: {e}")
        return {"error": f"AI API Error: {str(e)}"}


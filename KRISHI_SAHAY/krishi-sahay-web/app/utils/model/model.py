import os
import logging
import json
import base64
import requests
from .dict import return_disease, show, get_dict

api_key = os.getenv("GEMINI_API_KEY")

def predict_image_class(image_path):
    if not api_key:
        return {"error": "GEMINI_API_KEY is missing from environment variables."}
        
    try:
        # Read the image and encode it to base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
            
        # Call Gemini REST API directly to bypass any old SDK version issues
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
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
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": encoded_string
                            }
                        }
                    ]
                }
            ]
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        
        if response.status_code != 200:
            logging.error(f"Gemini API REST Error: {response_data}")
            return {"error": f"API Error {response.status_code}: {response_data.get('error', {}).get('message', 'Unknown')}"}
            
        try:
            result = response_data["candidates"][0]["content"]["parts"][0]["text"].strip().replace("\"", "").replace("`", "")
        except KeyError:
            return {"error": "Invalid response format from Gemini API."}
            
        logging.info(f"Gemini predicted: {result}")
        
        if "healthy" in result.lower():
            return "healthy"
            
        valid_keys = [
            "Downey Mildew", 
            "Pepper__bell___Bacterial_spot", 
            "Tomato__Tomato_YellowLeaf__Curl_Virus", 
            "Tomato__Tomato_mosaic_virus"
        ]
        
        if result in valid_keys:
            return get_dict(result)
            
        for key in valid_keys:
            if key.lower() in result.lower() or result.lower() in key.lower():
                return get_dict(key)
                
        return {"error": f"Model could not confidently classify the disease. It said: {result}"}
        
    except Exception as e:
        logging.error(f"Gemini prediction failed: {e}")
        return {"error": f"AI API Error: {str(e)}"}


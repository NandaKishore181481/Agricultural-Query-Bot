import logging
from flask import current_app, jsonify
import json
import requests
from deep_translator import GoogleTranslator
import asyncio
import google.generativeai as genai

# database
from .database import add_user, get_user, update_preferences

# medicine
from .product.finder import search_medicine_for_disease

# model
from .model.model import predict_image_class

# Third party whatsapp module
from heyoo import WhatsApp

from app.services.openai_service import generate_response, client
import re

from dotenv import load_dotenv
import os

load_dotenv()
ACCESS_TOKEN = os.getenv("ACCESS_TOKEN")
messenger = WhatsApp(ACCESS_TOKEN)

# to store user info
user_dict = {}


class User:
    def __init__(self, wa_name, wa_no):
        self.name = wa_name
        self.reg_no = wa_no
        self.lang = None


# Translate the data
def translate_dict(data, lang="en"):
    if isinstance(data, str):
        return GoogleTranslator(source="auto", target=lang).translate(data)
    elif isinstance(data, list):
        return [translate_dict(item, lang) for item in data]
    elif isinstance(data, dict):
        return {key: translate_dict(value, lang) for key, value in data.items()}
    else:
        return data


def log_http_response(response):
    logging.info(f"Status: {response.status_code}")
    logging.info(f"Content-type: {response.headers.get('content-type')}")
    logging.info(f"Body: {response.text}")


def get_text_message_input(recipient, type, text, lang="en"):
    # Normal text for image inputs
    # TODO Analyise the image and genrated the diesease output
    if type == "image":
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }
        )

    # Sents Template with buttons
    elif type == "text":
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "template",
                "template": {
                    "namespace": "f701d0b1_eed6_466e_bedb_128a0e30871b",
                    "name": "features",
                    "language": {"code": "en_US" if lang == "en" else lang, "policy": "deterministic"},
                },
            }
        )

    elif type == "first":
        logging.info("First Message")
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {
                        "text": "Please select your preferred language:\nकृपया अपनी पसंदीदा भाषा चुनें:\nదయచేసి మీకు కావలసిన భాషను ఎంచుకోండి:"
                    },
                    "action": {
                        "buttons": [
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "lang_en",
                                    "title": "English"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "lang_hi",
                                    "title": "हिंदी"
                                }
                            },
                            {
                                "type": "reply",
                                "reply": {
                                    "id": "lang_te",
                                    "title": "తెలుగు"
                                }
                            }
                        ]
                    }
                }
            }
        )

    elif type == "button":
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient,
                "type": "text",
                "text": {"preview_url": False, "body": text},
            }
        )

    elif type == "prediction":
        logging.info("Prediction")
        logging.info(f"{text=}")

        if lang == "en":
            return json.dumps(
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": f" 🦠 *Disease* : {text['Name']}\n📃 *Description* : {text['Description']}\n🔴 *Lack Of* : {text['RequiredNutirents']}  \n👀 *Symptoms* : {text['Symptoms']}\n🧪 *Chemical Solution* : {text['Solutions']['Chemical'][0]}\n☘️ *Organic Solution* : {text['Solutions']['Organic'][0]}",
                    },
                }
            )

        elif lang == "hi":
            return json.dumps(
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": f" 🌿 *पौधा* : {text.get('Plant', 'Unknown')}\n 🦠 *रोग* : {text['Name']}\n📃 *विवरण* : {text['Description']}\n🔴 *कमी* : {text['RequiredNutirents']}  \n👀 *लक्षण* : {text['Symptoms']}\n🧪 *रासायनिक उपाय* : {text['Solutions']['Chemical'][0]}\n☘️ *जैविक उपाय* : {text['Solutions']['Organic'][0]}",
                    },
                }
            )

        elif lang == "te":
            return json.dumps(
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": f" 🌿 *మొక్క* : {text.get('Plant', 'Unknown')}\n 🦠 *వ్యాధి* : {text['Name']}\n📃 *వివరణ* : {text['Description']}\n🔴 *లోపం* : {text['RequiredNutirents']}  \n👀 *లక్షణాలు* : {text['Symptoms']}\n🧪 *రసాయన పరిష్కారం* : {text['Solutions']['Chemical'][0]}\n☘️ *సేంద్రీయ పరిష్కారం* : {text['Solutions']['Organic'][0]}",
                    },
                }
            )

        else:
            return json.dumps(
                {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": recipient,
                    "type": "text",
                    "text": {
                        "preview_url": False,
                        "body": f" 🌿 *Plant* : {text.get('Plant', 'Unknown')}\n 🦠 *Disease* : {text['Name']}\n📃 *Description* : {text['Description']}\n🔴 *Lack Of* : {text['RequiredNutirents']}  \n👀 *Symptoms* : {text['Symptoms']}\n🧪 *Chemical Solution* : {text['Solutions']['Chemical'][0]}\n☘️ *Organic Solution* : {text['Solutions']['Organic'][0]}",
                    },
                }
            )
    elif type == "Catalogue":
        return json.dumps(
            {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": "+918075962393",
                "type": "interactive",
                "interactive": {
                    "type": "product_list",
                    "header": {"type": "text", "text": "Explore Our Products"},
                    "body": {"text": "Click To View Items"},
                    "action": {
                        "catalog_id": "1755905158245374",
                        "sections": [
                            {
                                "title": "Tata Rallis",
                                "product_items": [
                                    {"product_retailer_id": "fflhvn18uk"}
                                ],
                            }
                        ],
                    },
                },
            }
        )





def send_message(data):
    headers = {
        "Content-type": "application/json",
        "Authorization": f"Bearer {current_app.config['ACCESS_TOKEN']}",
    }

    url = f"https://graph.facebook.com/{current_app.config['VERSION']}/{current_app.config['PHONE_NUMBER_ID']}/messages"

    logging.info(f"Data Sending {data=}")
    try:
        response = requests.post(
            url, data=data, headers=headers, timeout=10
        )  # 10 seconds timeout as an example
        # print("RESPONSE:", response.content)
        response.raise_for_status()  # Raises an HTTPError if the HTTP request returned an unsuccessful status code
    except requests.Timeout:
        logging.error("Timeout occurred while sending message")
        return jsonify({"status": "error", "message": "Request timed out"}), 408
    except (
        requests.RequestException
    ) as e:  # This will catch any general request exception
        logging.error(f"Request failed due to: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500
    else:
        # Process the response as normal
        log_http_response(response)
        return response


def process_text_for_whatsapp(text):
    # Remove brackets
    pattern = r"\【.*?\】"
    # Substitute the pattern with an empty string
    text = re.sub(pattern, "", text).strip()

    # Pattern to find double asterisks including the word(s) in between
    pattern = r"\*\*(.*?)\*\*"

    # Replacement pattern with single asterisks
    replacement = r"*\1*"

    # Substitute occurrences of the pattern with the replacement
    whatsapp_style_text = re.sub(pattern, replacement, text)

    return whatsapp_style_text


def process_whatsapp_message(body):
    wa_no = messenger.get_mobile(body)
    wa_name = messenger.get_name(body)
    logging.debug(f"wa_no={wa_no}, wa_name={wa_name}")
    logging.debug("BODY received")
    # Added user to DB
    user = User(wa_no, wa_name)
    is_new = add_user(wa_no=wa_no, wa_name=wa_name)
    logging.info(f"{is_new=}")
    if is_new:
        # ── NEW USER: show language-selection template first ──
        # This sends the 'lang' WhatsApp template which has
        # three quick-reply buttons: English / हिंदी / తెలుగు
        logging.info("New user detected – sending language selection prompt")
        data = get_text_message_input(
            wa_no, "first", None
        )
        send_message(data)


    # TODO: Check the type of message
    message_type = messenger.get_message_type(body)
    message = body["entry"][0]["changes"][0]["value"]["messages"][0]
    logging.debug(f"{message=}")

    if message_type in ["button", "interactive"]:
        logging.info("Its a button or interactive message")
        if message_type == "button":
            message_body = message["button"]["text"]
        else:
            if message.get("interactive", {}).get("type") == "button_reply":
                message_body = message["interactive"]["button_reply"]["title"]
            else:
                message_body = ""
        logging.info(f"{message_body=}")

        if message_body == "English":
            update_preferences(wa_no=wa_no, preferences="en")
            response = "Language Upated"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

            message_type = "text"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

        elif message_body == "हिंदी":
            update_preferences(wa_no=wa_no, preferences="hi")
            response = "भाषा अपडेट की गई"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

            message_type = "text"
            data = get_text_message_input(
                wa_no, message_type, response, lang="hi"
            )
            send_message(data)

        elif message_body == "తెలుగు":
            update_preferences(wa_no=wa_no, preferences="te")
            response = "భాష అప్‌డేట్ చేయబడింది"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

            message_type = "text"
            data = get_text_message_input(
                wa_no, message_type, response, lang="te"
            )
            send_message(data)

        elif message_body == "रोग पहचान" or message_body == "వ్యాధి గుర్తింపు":
            response = {
                "en": "Send the picture of infected leaf ☘️",
                "hi": "संक्रमित पत्ते की तस्वीर भेजें ☘️",
                "te": "వ్యాధి సోకిన ఆకు చిత్రాన్ని పంపండి ☘️"
            }.get(get_user(wa_no=wa_no)[0], "Send the picture of infected leaf ☘️")
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

        elif message_body == "Disease detection":
            response = "Send the picture of infected leaf ☘️"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)
        elif message_body == "Fertilizers":
            response = "Nothing"
            message_type = "Catalogue"
            data = get_text_message_input(
                wa_no, message_type, response
            )
            send_message(data)

    elif message_type == "text":
        logging.info("Its a text message")
        message_body = message["text"]["body"]

        # If user types language change triggers, show the language menu
        if message_body.lower().strip() in ["language", "change language", "select language", "menu", "hi", "hello", "start"]:
            data = get_text_message_input(wa_no, "first", None)
            send_message(data)
            return

        # Get user language from DB
        user_record = get_user(wa_no=wa_no)
        user_lang = (user_record[0] if user_record and user_record[0] else "en")
        
        # print(f"User Lang: {user_lang}, Message: {message_body}")
        
        response = generate_response(message_body, wa_no, wa_name, lang=user_lang)
        data = get_text_message_input(
            wa_no, "button", response
        )
        send_message(data)

    elif message_type == "image":
        # Safely fetch user language; default to English if not set yet
        user_record = get_user(wa_no=wa_no)
        user_lang = (user_record[0] if user_record and user_record[0] else "en")
        logging.info(f"{user_lang=}")

        # ── Step 1: acknowledge receipt ──
        ack_map = {
            "en": "Analysing The Image ☘️",
            "hi": "छवि का विश्लेषण किया जा रहा है ☘️",
            "te": "చిత్రాన్ని విశ్లేషిస్తున్నాము ☘️",
        }
        ack_msg = ack_map.get(user_lang, "Analysing The Image ☘️")
        data = get_text_message_input(
            wa_no, "image", ack_msg
        )
        send_message(data)

        # ── Step 2: download & predict ──
        try:
            image = messenger.get_image(body)
            image_id, mime_type = image["id"], image["mime_type"]
            image_url = messenger.query_media_url(image_id)
            image_filename = messenger.download_media(image_url, mime_type)
            logging.info(f"Downloaded image: {image_filename}")
        except Exception as e:
            logging.error(f"Image download failed: {e}")
            err_map = {
                "en": "❌ Could not download the image. Please try again.",
                "hi": "❌ छवि डाउनलोड नहीं हो सकी। कृपया पुनः प्रयास करें।",
                "te": "❌ చిత్రాన్ని డౌన్‌లోడ్ చేయలేకపోయాము. దయచేసి మళ్ళీ ప్రయత్నించండి.",
            }
            data = get_text_message_input(
                wa_no, "button",
                err_map.get(user_lang, err_map["en"])
            )
            send_message(data)
            return

        prediction = predict_image_class(image_filename)
        # print(f"{prediction=}")

        # ── Step 3: handle prediction result ──
        if prediction is None:
            # Model unavailable or low-confidence result
            err_map = {
                "en": "❌ Sorry, I could not identify the disease. Please ensure the photo is clear and of a *Tomato* or *Pepper* leaf, as those are the only plants I currently support. ☘️",
                "hi": "❌ क्षमा करें, मैं रोग की पहचान नहीं कर सका। कृपया सुनिश्चित करें कि फोटो स्पष्ट है और *टमाटर* या *मिर्च* के पत्ते की है, क्योंकि मैं वर्तमान में केवल उन्हीं पौधों का समर्थन करता हूँ। ☘️",
                "te": "❌ క్షమించండి, నేను వ్యాధిని గుర్తించలేకపోయాను. దయచేసి ఫోటో స్పష్టంగా ఉందో లేదో మరియు అది *టమోటా* లేదా *మిర్చి* ఆకు అని నిర్ధారించుకోండి, ఎందుకంటే నేను ప్రస్తుతం ఆ మొక్కలకు మాత్రమే మద్దతు ఇస్తున్నాను. ☘️",
            }
            data = get_text_message_input(
                wa_no, "button",
                err_map.get(user_lang, err_map["en"])
            )
            send_message(data)
            return

        if prediction == "healthy":
            healthy_map = {
                "en": "✅ The plant appears to be healthy! ☘️",
                "hi": "✅ पौधा स्वस्थ दिखता है! ☘️",
                "te": "✅ మొక్క ఆరోగ్యంగా ఉన్నట్లు కనిపిస్తోంది! ☘️",
            }
            data = get_text_message_input(
                wa_no, "button",
                healthy_map.get(user_lang, healthy_map["en"])
            )
            send_message(data)
            return

        # ── Step 4: translate & send disease info ──
        if user_lang in ["hi", "te"]:
            prediction = translate_dict(prediction, lang=user_lang)
            # print(f"Translated to {user_lang}: {prediction=}")

        data = get_text_message_input(
            wa_no, "prediction", prediction, lang=user_lang
        )
        send_message(data)

    elif message_type in ["audio", "voice"]:
        logging.info(f"Its an {message_type} message")
        # Get user language from DB
        user_record = get_user(wa_no=wa_no)
        user_lang = (user_record[0] if user_record and user_record[0] else "en")

        try:
            # Extract audio ID manually to be safe
            message_data = body["entry"][0]["changes"][0]["value"]["messages"][0]
            audio_id = message_data.get("voice", message_data.get("audio", {})).get("id")
            mime_type = message_data.get("voice", message_data.get("audio", {})).get("mime_type", "audio/ogg")
            
            if not audio_id:
                raise Exception("Could not find audio/voice ID in message body")

            audio_url = messenger.query_media_url(audio_id)
            audio_filename = messenger.download_media(audio_url, mime_type)
            logging.info(f"Downloaded audio: {audio_filename}")

            # Transcribe the audio using Google Gemini (Free)
            gemini_key = os.getenv("GEMINI_API_KEY")
            if not gemini_key:
                raise Exception("GEMINI_API_KEY is missing in .env")
            
            genai.configure(api_key=gemini_key)
            
            with open(audio_filename, "rb") as f:
                audio_bytes = f.read()
                
            audio_data = {
                "mime_type": "audio/ogg",
                "data": audio_bytes
            }
            
            fallback_models = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-pro-latest"]
            response_trans = None
            
            for model_name in fallback_models:
                try:
                    model = genai.GenerativeModel(model_name)
                    response_trans = model.generate_content(
                        ["Please transcribe this audio exactly as it is spoken, in the same language as the speaker.", audio_data],
                        request_options={"timeout": 5}
                    )
                    break
                except Exception as e:
                    logging.warning(f"Transcription model {model_name} failed: {str(e)}")
            
            if response_trans is None:
                raise Exception("All fallback transcription models failed.")
                
            message_body = response_trans.text
            logging.info(f"Transcribed audio with Gemini: {message_body}")

            # Process as a text message
            response = generate_response(message_body, wa_no, wa_name, lang=user_lang)
            data = get_text_message_input(
                wa_no, "button", response
            )
            send_message(data)

        except Exception as e:
            logging.error(f"Audio processing failed: {e}")
            err_msg = {
                "en": "❌ Sorry, I couldn't process your voice message.",
                "hi": "❌ क्षमा करें, मैं आपके ध्वनि संदेश को संसाधित नहीं कर सका।",
                "te": "❌ క్షమించండి, నేను మీ వాయిస్ సందేశాన్ని ప్రాసెస్ చేయలేకపోయాను."
            }.get(user_lang, "❌ Sorry, I couldn't process your voice message.")
            data = get_text_message_input(
                wa_no, "button", err_msg
            )
            send_message(data)


def is_valid_whatsapp_message(body):
    """
    Check if the incoming webhook event has a valid WhatsApp message structure.
    """
    return (
        body.get("object")
        and body.get("entry")
        and body["entry"][0].get("changes")
        and body["entry"][0]["changes"][0].get("value")
        and body["entry"][0]["changes"][0]["value"].get("messages")
        and body["entry"][0]["changes"][0]["value"]["messages"][0]
    )

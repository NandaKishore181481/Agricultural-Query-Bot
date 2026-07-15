from openai import OpenAI
from app.utils.database import get_thread, save_thread
from dotenv import load_dotenv
import os
import logging

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Connect to OpenRouter using the OpenAI-compatible API
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Model to use (free tier on OpenRouter)
MODEL = "openrouter/free"

def get_system_prompt(lang="en"):
    prompts = {
        "en": "You are Krishi Sahay, a helpful agricultural expert assistant. Assist farmers with queries about crop diseases, fertilizers, and general farming practices. Keep responses concise and practical. Reply in English.",
        "hi": "आप कृषि सहाय हैं, एक सहायक कृषि विशेषज्ञ सहायक। किसानों को फसल रोगों, उर्वरकों और सामान्य खेती के तरीकों के बारे में प्रश्नों के साथ सहायता करें। उत्तर संक्षिप्त और व्यावहारिक रखें। हिंदी में उत्तर दें।",
        "te": "మీరు కృషి సహాయ్, ఒక సహాయక వ్యవసాయ నిపుణుడు. పంట తెగుళ్లు, ఎరువులు మరియు సాధారణ వ్యవసాయ పద్ధతుల గురించి అడిగే ప్రశ్నలకు రైతులకు సహాయం చేయండి. సమాధానాలను సంక్షిప్తంగా మరియు ఆచరణాత్మకంగా ఉంచండి. తెలుగులో సమాధానం ఇవ్వండి."
    }
    return prompts.get(lang, prompts["en"])

def check_if_thread_exists(wa_id):
    """Check if a conversation history exists for this user in the DB."""
    return get_thread(wa_id)


def store_thread(wa_id, messages):
    """Store conversation history for a user in the DB."""
    save_thread(wa_id, messages)


def generate_response(message_body, wa_id, name, lang="en"):
    """Generate a response using OpenRouter chat completions."""
    # Load existing conversation or start fresh
    messages = check_if_thread_exists(wa_id)

    system_prompt = get_system_prompt(lang)

    if messages is None:
        logging.info(f"Creating new conversation for {name} with wa_id {wa_id}")
        messages = [{"role": "system", "content": system_prompt}]
    else:
        logging.info(f"Retrieving existing conversation for {name} with wa_id {wa_id}")
        # Update system prompt in case language changed
        if messages[0]["role"] == "system":
            messages[0]["content"] = system_prompt

    # Add the user's new message
    messages.append({"role": "user", "content": message_body})

    try:
        # Call OpenRouter API
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=500,
        )

        new_message = response.choices[0].message.content
        logging.info(f"Generated message: {new_message}")

        # Save assistant reply to conversation history
        messages.append({"role": "assistant", "content": new_message})

        # Keep only last 20 messages to avoid token overflow
        if len(messages) > 21:
            messages = [messages[0]] + messages[-20:]

        store_thread(wa_id, messages)

        return new_message

    except Exception as e:
        logging.error(f"OpenRouter API error: {e}")
        return {
            "en": "Sorry, I'm having trouble processing your request.",
            "hi": "क्षमा करें, मुझे आपके अनुरोध को संसाधित करने में समस्या हो रही है।",
            "te": "క్షమించండి, మీ అభ్యర్థనను ప్రాసెస్ చేయడంలో నాకు సమస్య ఉంది."
        }.get(lang, "Sorry, I'm having trouble processing your request.")

import logging
import json

from flask import Blueprint, request, jsonify, current_app, session, render_template

from .decorators.security import signature_required
from .utils.core_utils import (
    process_whatsapp_message,
    is_valid_whatsapp_message,
)
import os
from werkzeug.utils import secure_filename
from .services.openai_service import generate_response
from .utils.model.model import predict_image_class
from .utils.core_utils import translate_dict

webhook_blueprint = Blueprint("webhook", __name__)


def handle_message():
    """
    Handle incoming webhook events from the WhatsApp API.

    This function processes incoming WhatsApp messages and other events,
    such as delivery statuses. If the event is a valid message, it gets
    processed. If the incoming payload is not a recognized WhatsApp event,
    an error is returned.

    Every message send will trigger 4 HTTP requests to your webhook: message, sent, delivered, read.

    Returns:
        response: A tuple containing a JSON response and an HTTP status code.
    """
    body = request.get_json()
    # logging.info(f"request body: {body}")

    # Check if it's a WhatsApp status update
    if (
        body.get("entry", [{}])[0]
        .get("changes", [{}])[0]
        .get("value", {})
        .get("statuses")
    ):
        logging.info("Received a WhatsApp status update.")
        return jsonify({"status": "ok"}), 200

    try:
        if is_valid_whatsapp_message(body):
            process_whatsapp_message(body)
            return jsonify({"status": "ok"}), 200
        else:
            # if the request is not a WhatsApp API event, return an error
            return (
                jsonify({"status": "error", "message": "Not a WhatsApp API event"}),
                404,
            )
    except json.JSONDecodeError:
        logging.error("Failed to decode JSON")
        return jsonify({"status": "error", "message": "Invalid JSON provided"}), 400


# Required webhook verifictaion for WhatsApp
def verify():
    # Parse params from the webhook verification request
    mode = request.args.get("hub.mode")
    token = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    # Check if a token and mode were sent
    if mode and token:
        # Check the mode and token sent are correct
        if mode == "subscribe" and token == current_app.config["VERIFY_TOKEN"]:
            # Respond with 200 OK and challenge token from the request
            logging.info("WEBHOOK_VERIFIED")
            return challenge, 200
        else:
            # Responds with '403 Forbidden' if verify tokens do not match
            logging.info("VERIFICATION_FAILED")
            return jsonify({"status": "error", "message": "Verification failed"}), 403
    else:
        # Responds with '400 Bad Request' if verify tokens do not match
        logging.info("MISSING_PARAMETER")
        return jsonify({"status": "error", "message": "Missing parameters"}), 400


@webhook_blueprint.route("/webhook", methods=["GET"])
def webhook_get():
    return verify()


@webhook_blueprint.route("/webhook", methods=["POST"])
@signature_required
def webhook_post():
    return handle_message()


@webhook_blueprint.route("/", methods=["GET"])
def index():
    return render_template("index.html")


@webhook_blueprint.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    message = data.get("message", "")
    lang = data.get("lang", "en")
    
    # We pass a dummy 'wa_no' since web users don't have a phone number yet.
    # In a real app we'd use session IDs.
    wa_no = session.get("user_id", "web_user")
    wa_name = "Web User"
    
    response_text = generate_response(message, wa_no, wa_name, lang=lang)
    return jsonify({"response": response_text})


@webhook_blueprint.route("/api/predict", methods=["POST"])
def api_predict():
    try:
        if "image" not in request.files:
            return jsonify({"error": "No image provided"}), 400
            
        file = request.files["image"]
        lang = request.form.get("lang", "en")
        
        if file.filename == "":
            return jsonify({"error": "Empty filename"}), 400
            
        filename = secure_filename(file.filename)
        filepath = os.path.join(os.getcwd(), filename)
        file.save(filepath)
        
        prediction = predict_image_class(filepath)
        
        if prediction is None:
            return jsonify({"error": "Could not identify the plant. Please make sure it is a tomato or pepper leaf."}), 400
            
        if isinstance(prediction, dict) and "error" in prediction:
            return jsonify({"error": prediction["error"]}), 400
            
        if prediction == "healthy":
            healthy_map = {
                "en": "✅ The plant appears to be healthy! ☘️",
                "hi": "✅ यह पौधा स्वस्थ लग रहा है! ☘️",
                "te": "✅ ఈ మొక్క ఆరోగ్యంగా ఉన్నట్లు కనిపిస్తోంది! ☘️",
            }
            return jsonify({"status": "healthy", "message": healthy_map.get(lang, healthy_map["en"])})
            
        if lang in ["hi", "te"]:
            prediction = translate_dict(prediction, lang=lang)
            
        return jsonify({"status": "disease", "prediction": prediction})
    except Exception as e:
        import traceback
        return jsonify({"error": f"Server Crash: {str(e)}\n{traceback.format_exc()}"}), 400

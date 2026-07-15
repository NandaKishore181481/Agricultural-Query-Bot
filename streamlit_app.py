import sys
import os

# Add the web app directory to the system path so we can import our existing modules
sys.path.append(os.path.join(os.path.dirname(__file__), "KRISHI_SAHAY", "krishi-sahay-web"))

import streamlit as st
import tempfile
from app.services.openai_service import generate_response
from app.utils.model.model import predict_image_class
from app.utils.core_utils import translate_dict
from app.utils.database import initialize_database

# Initialize the database so the 'threads' and 'users' tables are created
initialize_database()

st.set_page_config(page_title="Krishi Sahay", page_icon="☘️", layout="centered")

st.title("Krishi Sahay ☘️")
st.markdown("**Your AI Crop Doctor**")

# Language Selection
lang_options = {"English": "en", "हिंदी": "hi", "తెలుగు": "te"}
selected_lang = st.selectbox("Select Language / भाषा चुनें / భాషను ఎంచుకోండి", list(lang_options.keys()))
lang_code = lang_options[selected_lang]

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"], unsafe_allow_html=True)

# Image upload section
uploaded_file = st.file_uploader("Upload a leaf image (Tomato or Pepper) for disease detection 📷", type=["jpg", "jpeg", "png"])
if uploaded_file is not None:
    # Process the uploaded image only once
    if "last_uploaded" not in st.session_state or st.session_state.last_uploaded != uploaded_file.name:
        st.session_state.last_uploaded = uploaded_file.name
        
        with st.chat_message("user"):
            st.image(uploaded_file, caption="Uploaded Image", width=300)
            st.session_state.messages.append({"role": "user", "content": f"Uploaded image: {uploaded_file.name}"})
            
        with st.chat_message("assistant"):
            with st.spinner("Analyzing image..."):
                # Save uploaded file to temp file for prediction
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    tmp_path = tmp_file.name
                
                prediction = predict_image_class(tmp_path)
                os.unlink(tmp_path)
                
                if prediction is None:
                    response_text = "Could not identify the plant. Please make sure it is a tomato or pepper leaf."
                elif prediction == "healthy":
                    healthy_map = {
                        "en": "✅ The plant appears to be healthy! ☘️",
                        "hi": "✅ पौधा स्वस्थ दिखता है! ☘️",
                        "te": "✅ మొక్క ఆరోగ్యంగా ఉన్నట్లు కనిపిస్తోంది! ☘️",
                    }
                    response_text = healthy_map.get(lang_code, healthy_map["en"])
                else:
                    p = prediction
                    if lang_code in ["hi", "te"]:
                        p = translate_dict(p, lang=lang_code)
                        
                    response_text = f"**Identified:** {p.get('Name', 'Unknown')}<br>"
                    response_text += f"**Plant:** {p.get('Plant', 'Unknown')}<br><br>"
                    response_text += f"{p.get('Description', '')}<br><br>"
                    response_text += f"**Symptoms:** {p.get('Symptoms', '')}<br><br>"
                    
                    sols = p.get('Solutions', {})
                    if sols:
                        response_text += "**Solutions:**<br>"
                        if 'Chemical' in sols:
                            response_text += f"🧪 *Chemical:* {' '.join(sols['Chemical'])}<br>"
                        if 'Organic' in sols:
                            response_text += f"🌿 *Organic:* {' '.join(sols['Organic'])}<br>"
                            
                st.markdown(response_text, unsafe_allow_html=True)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

# Chat input
if prompt := st.chat_input("Ask me anything about agriculture..."):
    # Display user message
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    # Display bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            response = generate_response(prompt, "streamlit_user", "Web User", lang=lang_code)
            st.markdown(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

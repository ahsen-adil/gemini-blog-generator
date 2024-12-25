import os
import streamlit as st
import google.generativeai as genai
from gtts import gTTS
import tempfile
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure the API key
api_key = os.getenv("API_KEY")
if not api_key:
    st.error("API_KEY is not set. Please add it to your environment or .env file.")
    st.stop()

genai.configure(api_key=api_key)

# Function to upload a file to Gemini
def upload_to_gemini(path, mime_type=None):
    """Uploads the given file to Gemini."""
    try:
        file = genai.upload_file(path, mime_type=mime_type)
        return file
    except Exception as e:
        st.error(f"File upload failed: {e}")
        return None

# Streamlit UI
st.title("Gemini AI Blog Post Generator with Voice")
st.write("Generate an engaging blog post using AI by providing a prompt. Optionally, upload an image to enhance the result. Get the response in both text and audio!")

# File upload section (optional for images)
uploaded_file = st.file_uploader("Upload an image (optional, e.g., JPEG, PNG)", type=["jpeg", "png"])

# Text area input for prompt
user_prompt = st.text_area("Enter your prompt", placeholder="Describe what you want the AI to generate.")

# Ensure the user has provided a prompt before generating
if st.button("Generate"):
    if not user_prompt.strip():
        st.error("Please enter a prompt.")
    else:
        try:
            # Handle uploaded file (if any)
            uploaded_gemini_file = None
            if uploaded_file is not None:
                with tempfile.NamedTemporaryFile(delete=False, suffix=f".{uploaded_file.name.split('.')[-1]}") as temp_file:
                    temp_file.write(uploaded_file.getbuffer())
                    temp_file_path = temp_file.name
                
                # Upload file to Gemini
                uploaded_gemini_file = upload_to_gemini(temp_file_path, mime_type="image/jpeg")
                if uploaded_gemini_file:
                    st.success(f"File uploaded successfully: {uploaded_gemini_file.uri}")

            # Configure the generation model
            generation_config = {
                "temperature": 0.9,
                "top_p": 0.95,
                "top_k": 40,
                "max_output_tokens": 8192,
                "response_mime_type": "text/plain",
            }

            model = genai.GenerativeModel(
                model_name="gemini-1.5-flash",
                generation_config=generation_config,
            )

            # Prepare the chat session
            chat_history = [{"role": "user", "parts": [user_prompt]}]
            if uploaded_gemini_file:
                chat_history[0]["parts"].insert(0, uploaded_gemini_file)

            chat_session = model.start_chat(history=chat_history)

            # Generate the response
            response = chat_session.send_message("Generate content")
            response_text = response.text

            # Display the generated blog post
            st.subheader("Generated Blog Post")
            st.write(response_text)

            # Convert response to audio
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                tts = gTTS(text=response_text, lang='en')
                tts.save(temp_audio.name)
                audio_path = temp_audio.name

            # Play the generated audio
            st.subheader("Listen to the Response")
            st.audio(audio_path, format="audio/mp3")

        except Exception as e:
            st.error(f"An error occurred: {e}")

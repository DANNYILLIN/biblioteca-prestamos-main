import os
import google.generativeai as genai
from dotenv import load_dotenv

# Cargar variables de tu .env
load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

print("Modelos disponibles para generar texto:")
for m in genai.list_models():
    if 'generateContent' in m.supported_generation_methods:
        print("-", m.name)
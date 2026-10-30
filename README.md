# Urdu ⇄ Malay Translator

Streamlit web app jo Urdu aur Malay ke darmiyan text aur voice translation karti hai.

## Features
- Urdu ⇄ Malay text translation (aur dusri languages bhi, dropdown se)
- Voice input (Whisper se speech-to-text)
- Translation ki awaz (text-to-speech)
- Urdu output right-to-left dikhta hai

## Setup (VS Code)

1. Project folder VS Code mein kholein (`File > Open Folder`).
2. Terminal kholein (`Ctrl + ` `) aur virtual environment banayein:

   ```bash
   python -m venv venv
   ```

3. Environment on karein:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Libraries install karein:

   ```bash
   pip install -r requirements.txt
   ```

5. App chalayein:

   ```bash
   streamlit run app.py
   ```

   Browser mein `http://localhost:8501` khul jayega.

## Notes
- Pehli baar chalane par Whisper `small` model download hota hai (lagbhag 480 MB).
- CPU par slow ho to `app.py` mein `"small"` ko `"base"` kar dein.
- `deep-translator` aur `gtts` unofficial hain. Client project ke liye official API use karein.

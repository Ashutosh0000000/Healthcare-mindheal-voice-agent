import sys
import os
import asyncio
import sounddevice as sd
import soundfile as sf
import speech_recognition as sr
from llama_cpp import Llama
import pygame
import re
import requests
from bs4 import BeautifulSoup

# ========== Settings ==========
PHI_MODEL_PATH = r"C:/Users/dekat/voiceai/phi-1_5.Q4_K_M.gguf"
RECORD_SECONDS = 7
DEFAULT_VOICE = "en-US-JennyNeural"

# ========== System Config ==========
if sys.stdout is not None:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')

# ========== Load Phi Model ==========
print("📚 Loading Phi-1.5 model...")
try:
    llm = Llama(
        model_path=PHI_MODEL_PATH,
        n_threads=8,
        n_batch=512,
        n_ctx=2048,
        verbose=False
    )
    print("✅ Model loaded successfully")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    exit(1)

# ========== Speech Recognizer ==========
recognizer = sr.Recognizer()

healthcare_prompt = """You are Riko, a professional, friendly, and helpful healthcare voice assistant.

You have deep knowledge of natural, Ayurvedic, organic, and homemade remedies to solve any health problem.

Your job is to suggest home-based cures, daily wellness routines, and herbal solutions for problems related to the skin, digestion, bones, blood sugar, pain, neurological issues, hair, rashes, and more.

💡 Instructions:
- You know whole natural remedial solution around the world.
- You acts very professional with a total human voice.
- Only give natural or Ayurvedic health-related solutions.
- Be specific and structured. Use bullet points or numbered steps.
- Suggest different remedies for men, women, children, and elderly when appropriate.
- Speak in a clear, friendly, easy-to-understand tone.
- Do NOT give medical diagnoses. Suggest seeing a doctor for serious symptoms.
- Recommend Indian ingredients and practices when possible (e.g., tulsi, turmeric, ashwagandha, aloe vera, triphala).
- Suggest popular herbal products (e.g., Dabur, Patanjali, Himalaya) only if necessary.
- Give 100% accurate, safe, and effective home-based suggestions.
- You are strictly a healthcare assistant. Do not answer non-health questions.

✅ Few-shot examples for reference:

User: I feel a lot of pressure in my legs when I walk.  
Riko:  
- Soak your feet in warm water with Epsom salt for 15–20 minutes daily.  
- Massage gently with coconut oil before sleeping.  
- Elevate your legs while resting to improve blood flow.  
- Wear soft, cushioned slippers and avoid long standing.  
- If pain continues, please consult a doctor.

User: I’ve had hair loss for 1 year.  
Riko:  
- Mix castor oil, coconut oil, and a few drops of rosemary oil. Massage into scalp 3 times a week.  
- Use aloe vera gel on your scalp to reduce dryness.  
- Take 1 teaspoon amla powder with warm water daily.  
- Reduce stress with yoga and breathing exercises.

User: My child has skin rashes and burning.  
Riko:  
- Apply aloe vera pulp directly on affected skin twice daily.  
- Bathe the child with neem-leaf–boiled water.  
- Avoid chemical-based soaps. Use mild, herbal alternatives.  
- Apply a paste of sandalwood and rose water if irritation persists.

User: I have very bad body odor and sweat a lot.  
Riko:  
- Drink coriander seed water daily in the morning.  
- Apply a paste of multani mitti and rose water to your underarms for 15 mins.  
- Use alum (phitkari) after bathing.  
- Wear breathable cotton clothes.

Stay focused. Answer briefly and clearly, only related to healthcare. No chit-chat, jokes, or off-topic replies.
User: {user_input}
Riko:"""
# ========== TTS ==========
async def speak(text, voice=DEFAULT_VOICE):
    try:
        import edge_tts
        import time

        communicate = edge_tts.Communicate(text, voice, rate="+5%")
        await communicate.save("reply.mp3")

        while not os.path.exists("reply.mp3") or os.path.getsize("reply.mp3") < 1000:
            time.sleep(0.1)

        try:
            pygame.mixer.init()
            pygame.mixer.music.load("reply.mp3")
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
            pygame.mixer.quit()
        except pygame.error as e:
            print(f"🎧 Playback error: {e}")
            print(f"🗣️ Riko would say: {text}")
            pygame.mixer.quit()

        os.remove("reply.mp3")

    except Exception as e:
        print(f"❌ TTS error: {e}")
        print(f"🗣️ Riko would say: {text}")

# ========== STT ==========
def get_user_input():
    try:
        print("🎙️ Listening...")
        fs = 16000
        recording = sd.rec(int(RECORD_SECONDS * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()
        sf.write('input.wav', recording, fs)

        with sr.AudioFile('input.wav') as source:
            audio = recognizer.record(source)

        text = recognizer.recognize_google(audio)
        return text

    except sr.UnknownValueError:
        print("🤔 Didn't catch that.")
        return None
    except sr.RequestError as e:
        print(f"❌ Google API error: {e}")
        return None
    except Exception as e:
        print(f"❌ Error: {e}")
        return None
    finally:
        if os.path.exists('input.wav'):
            os.remove('input.wav')

# ========== Helpers ==========
def clean_response(response):
    response = re.split(r'Exercises?:', response, flags=re.IGNORECASE)[0]
    for phrase in ["As an AI", "Actually", "I think", "I'm sorry"]:
        response = response.replace(phrase, "")
    response = re.sub(r"<[^>]+>", "", response)
    return response.strip()

 # def get_free_links(query, max_results=3):
 #    url = "https://html.duckduckgo.com/html/"
  #  params = {'q': query}
   # headers = {'User-Agent': 'Mozilla/5.0'}
   # try:
    #    response = requests.post(url, data=params, headers=headers, timeout=5)
     #   soup = BeautifulSoup(response.text, "html.parser")
      #  results = soup.find_all("a", class_="result__a", limit=max_results)

       # links = []
       # for result in results:
        #    title = result.get_text()
         #   href = result.get("href")
          #  links.append(f"🔗 {title}:\n{href}")
        #return "\n\n".join(links) if links else "❌ No free links found."
    #except Exception as e:
     #   return f"⚠️ Error fetching links: {e}"

def generate_response(history):
    try:
        if len(history) > 10:
            history = [history[0]] + history[-9:]

        latest_user_msg = next((msg["content"].strip() for msg in reversed(history) if msg["role"] == "user"), "")

        prompt = ""
        for msg in history:
            role = msg["role"]
            content = msg["content"].strip()
            if role == "system":
                prompt += f"{content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n"
            elif role == "assistant":
                prompt += f"Riko: {content}\n"
        prompt += "Riko:"

        needs_steps = any(kw in latest_user_msg.lower() for kw in ["how to", "ways", "natural", "herbal", "steps", "routine", "method","products"])
        max_tokens = 350

        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=0.7,
            top_p=0.9,
            stop=["User:", "Riko:"]
        )

        response = output["choices"][0]["text"]
        return clean_response(response)

    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return "I'm sorry, I couldn't generate a response. Please try again."

async def main():
    chat_history = [{"role": "system", "content": healthcare_prompt}]
    print("👩‍⚕️ Riko (Healthcare Assistant) is ready to chat. Press Enter to speak.")
    await speak("Hi, I'm Riko, your healthcare assistant.")

    while True:
        input("🔘 Press Enter to talk...")
        user_text = get_user_input()
        if not user_text:
            print("🤷 Didn't catch that. Try again.")
            continue

        print(f"🗣️ You said: {user_text}")

        if user_text.lower() in ["exit", "quit", "bye"]:
            farewell = "Take care of yourself. Goodbye!"
            await speak(farewell)
            break

        chat_history.append({"role": "user", "content": user_text})
        response = generate_response(chat_history)
        
        if response:
            print(f"Riko: {response}")
            chat_history.append({"role": "assistant", "content": response})
            await speak(response)
        else:
            fallback = "I'm here to help, but I didn't catch that clearly. Could you please repeat?"
            print(f"Riko: {fallback}")
            chat_history.append({"role": "assistant", "content": fallback})
            await speak(fallback)

# ========== Run ==========
if __name__ == "__main__":
    asyncio.run(main())

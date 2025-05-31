
# ESP32 AI Storytelling Device - System Design (MVP)

## 🧸 Overview

This system powers an ESP32-based interactive storytelling device for children. A parent uses a mobile app to send story prompts. The backend generates a custom story using AI, converts it to speech and visuals, and streams them to the device in sync.

---

## 📐 System Architecture

```
Parent App ↔ FastAPI Server ↔ Firebase Auth + Storage
                         ↘
                        OpenAI GPT (Text)
                         ↘
                     ElevenLabs (TTS)
                         ↘
                 Image Generator (DALL·E, SDXL, etc.)
                         ↘
                    Manifest + Media → ESP32
```

---

## 🎯 Components and Responsibilities

### 1. Parent Mobile App
- Authenticates via **Firebase Auth**.
- Connects to **FastAPI WebSocket**.
- Sends:
  ```json
  {
    "firebase_token": "<idToken>",
    "prompt": "Tell a bedtime story about a rabbit and a spaceship."
  }
  ```
- Receives:
  - Final story preview.
  - Playback manifest.
  - Story play confirmation.

---

### 2. FastAPI Backend

#### Key Tasks:
- **Validate Firebase ID token** (one-time).
- Use **OpenAI GPT-4** to generate story.
- **Segment story** into scenes.
- For each scene:
  - Generate **voice** via **ElevenLabs**.
  - Generate **image** using AI.
- Upload media to **Firebase Storage**.
- Save logs in **Firebase Firestore**.
- Build and send a **playback manifest**.

#### Manifest Format
```json
{
  "story_id": "rabbit_spaceship_001",
  "segments": [
    {
      "type": "image",
      "url": "https://firebase.storage.com/story1/scene1.jpg",
      "start": 0
    },
    {
      "type": "audio",
      "url": "https://firebase.storage.com/story1/scene1.mp3",
      "start": 0
    },
    {
      "type": "image",
      "url": "https://firebase.storage.com/story1/scene2.jpg",
      "start": 12000
    }
  ]
}
```

> 🔎 **Why this format?**  
> - Lightweight and flat (easy for ESP32 to parse)  
> - All timing based on a single clock (`millis()`)  
> - No concurrency or complex scheduling required on device  

---

### 3. Firebase Platform

#### Firebase Auth
- Handles secure, low-code user auth for mobile app.

#### Firebase Storage
- Hosts images (`.jpg`) and audio (`.mp3`/`.ogg`) generated for each story.

#### Firebase Firestore (Optional)
- Logs story usage, device status, user feedback, etc.

---

### 4. ESP32 Device (Display + Audio)

#### Capabilities
- Wi-Fi connection.
- Screen (TFT, ST7789, etc.).
- Audio output (I2S DAC, external speaker).

#### Responsibilities
- Connect to backend WebSocket using user token.
- Receive `manifest.json`.
- Download all media files via HTTP.
- Store in SPIFFS or PSRAM.
- Use `millis()` to schedule and sync:
  - **Audio playback**
  - **Image display**
- Report final status to backend.

#### Local FSM
```
[ INIT ] → [ DOWNLOAD MEDIA ] → [ READY ] → [ PLAYBACK ] → [ DONE ]
```

#### Playback Logic (Pseudo)
```cpp
if (millis() >= segment[current].start) {
   if (segment[current].type == "image")
      showImage(segment[current].url);
   if (segment[current].type == "audio")
      playAudio(segment[current].url);
   current++;
}
```

> 🛠️ **Libraries**
> - JSON: `ArduinoJson`
> - HTTP: `HTTPClient`
> - Image: `TFT_eSPI` or `LVGL`
> - Audio: `ESP32-audioI2S`

---

## 📦 Asset Strategy

- All media are uploaded with unique URLs:
  ```
  /stories/<story_id>/scene<N>.mp3
  /stories/<story_id>/scene<N>.jpg
  ```
- Manifest is either:
  - Pushed via WebSocket, or
  - Fetched from a static URL.

---

## 💡 Design Principles

| Design Goal | Approach |
|-------------|----------|
| MVP Simplicity | Minimize on-device logic |
| Sync Audio + Visual | Precompute timings server-side |
| Lightweight Protocol | Flat JSON manifest, HTTP for assets |
| Fault Tolerance | ESP caches media before playback |
| Offline Mode | Replay last manifest on boot if network fails |

---

## 🔒 Security

- Firebase ID token used to validate users.
- Firebase Storage rules scoped per UID.
- WebSocket traffic encrypted via WSS.
- ESP32 only allowed to read media files, not write.

---

## 🧪 Development Recommendations

- Use **ESP32-WROVER** (with PSRAM) for higher memory.
- Pre-generate and cache a few example stories.
- Use compressed JPEGs and mono audio (`44.1kHz`, 16-bit).
- Benchmark media download + playback performance.
- Keep manifest < 10 KB and media bundle < 5 MB.

---

## 📈 Future Enhancements

- Streaming audio (instead of full download).
- Story personalization (age, tone, etc.).
- Device touchscreen for interactivity.
- Offline media preloading for travel use.
- Analytics dashboard for parents.

---

## 🧾 Sample Workflow

1. Parent logs in → sends prompt.
2. Server responds with manifest.
3. ESP receives manifest and downloads files.
4. ESP starts playback, showing images + playing audio.
5. ESP sends `{ story_id, status: "done" }` to server.

---

## 📁 Folder Structure

```
/server/
  - main.py (FastAPI WS backend)
  - ai_utils.py (OpenAI, ElevenLabs, ImageGen)
  - manifest_builder.py
  - firebase_utils.py

/esp32/
  - main.ino
  - manifest_parser.cpp
  - audio_player.cpp
  - image_renderer.cpp

/app/
  - StoryPromptScreen.tsx
  - WebSocketClient.ts
  - FirebaseAuth.ts

/assets/
  - example_manifest.json
```

---

## 🧠 TL;DR

This MVP system leverages AI + ESP32 with a simple manifest design to synchronize stories for children using audio + visuals. All heavy lifting is done on the server. ESP32 remains lightweight, deterministic, and offline-friendly — ideal for scalable early-stage deployment.

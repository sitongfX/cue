# Cue

**Live answer cues for conversations.** Cue listens to a conversation, transcribes both sides in real time, and when someone asks you something it shows a line you can say right away, plus a few supporting points, grounded in your own materials.

It's a single web page: no server, no build step. Everything runs in your browser.

## Use cases

- **Client and sales calls**: pricing, timelines, "how are you different from X?" Your product facts are on screen the moment the question lands.
- **Team meetings and reviews**: quick, accurate answers about your project's numbers and decisions.
- **Q&A after a talk or demo**: rehearse the likely questions beforehand; your prepared answer appears instantly when one comes up.
- **Support and office hours**: clear, step-by-step answers from your FAQ.
- **Cross-language calls**: live translation of the other side (Chinese ⇄ English) under every line.

## Features

- **Microphone first, no screen-share prompt**: *Start listening* uses only the microphone. On a call with headphones, tap **+ Meeting audio** at any time to add the meeting tab's sound (Chrome on desktop); Cue keeps the audio and drops the picture. On phones, the microphone hears everyone in the room.
- **Conversation context**: *Prep* has fields for who you're talking to, what it's about and what you want out of it; they go into every answer, follow-up, recap and speaker-labelling prompt.
- **English-first prompts**: all prompts are written in English (models follow English instructions best), with a spoken-English style (short sentences, contractions, no filler). The answer language follows the conversation by default, so English questions get English answers and Chinese questions get Chinese answers.
- **Full answers, not just bullets**: each answer has a one-line reply to say first, a complete spoken paragraph you can read out, then the key facts as points (Brief / Standard / Detailed / Cue-card in Settings).
- **Practise what you were actually asked**: after a call, one tap turns the other side's questions into a practice set (read aloud, answer by voice, get scored).
- **Searchable history**: search past conversations, including complete transcripts; titles come from the follow-up summary.
- **New conversation (N)**: saves the current one to History and starts clean, even while listening.
- **Hybrid recognition**: next to Gemini Live (mic only), the browser's built-in recognizer listens a few hundred ms ahead to spot questions and start drafting early, and takes over automatically if Gemini stops returning words while someone is talking. Duplicates are skipped when Gemini recovers.
- **Timing breakdown**: every answer shows recognition / detection / model time, so you can see where a delay comes from.
- **Model racing**: live answers start on the model that has been fastest for you; if no words arrive within 0.65 s (or a model errors), a backup model is asked in parallel, the first to stream wins and the rest are cancelled. Speeds are learned per connection, so a slow or overloaded model drops down the list automatically.
- **Automatic answers, as early as possible**: when the other side asks a question (with or without a question mark), an answer starts streaming right away. Cue even starts drafting from the words heard so far while they're still finishing the question; if the final question matches, the draft is kept. Each answer shows how fast it was ("Ready before they finished" or "0.6 s after they finished").
- **Something to say in the first second**: while the full answer streams in, Cue shows a natural opener that fits the question type (pricing, comparison, timing, "why", a concern…), so you're never silent.
- **Several questions at once**: if they ask two or three things in one breath, each one becomes a chip that's crossed off as you answer it, and the AI answers them in order.
- **Next point to say**: once you start answering, points you've covered are crossed out and the next one is highlighted, updated as you speak.
- **Live coaching while you speak**: Cue compares what you're saying with the question and your materials, and shows *Add:* (the most important missing point) or *Fix:* (something you got wrong), about a second after you pause.
- **Live speaking coach (while you talk)**: a small bar appears the moment you start speaking, with your turn timer, pace (chars/min or wpm), filler count and one instant tip: wrap up after ~45 s, slow down, sound more certain, add a number, or the next point to cover. Tips are computed locally, so they update every half second with no model call; AI *Add/Fix* coaching is layered on top.
- **Learns on your device**: a small logistic-regression model in the page learns which lines are questions *for you*: tapping a line to answer it teaches "yes", **Not a question** (X) teaches "no", and Space on a missed line teaches "yes". It starts from the built-in rules and is capped so one example can't override them. Cue also learns your preferred answer style from the follow-ups you pick (shorter / more detail / examples) and tunes how early it drafts answers from how often its early drafts are kept. *Prep → What Cue has learned about you* shows all of it, with a reset button.
- **Floating teleprompter**: the floating window (desktop Chrome) shows only the opener, the remaining points with *Next* enlarged, and the speaking coach, so it can sit next to your camera.
- **Your data, exportable**: materials, your past answers and everything Cue has learned live in this browser's IndexedDB. *Export materials* backs them up in one JSON file; *Export training data* saves the labelled "partial question → was the early draft kept" pairs collected during calls.
- **Rescue me (R)**: stuck or just said something wrong mid-answer? One tap gives you one sentence to say next: it corrects the slip using your materials or bridges back to your strongest point.
- **Remembers how you answered**: after each answer, the question and what you actually said are saved to your materials ("My past answers"). The next similar question shows your own wording instantly, so Cue gets more personal the more you use it.
- **Session stats**: when you stop, a scorecard shows answers, speed after they finished, points covered, talk share, filler words and longest turn, with arrows comparing to your previous session and one thing to try next time.
- **Tell you and them apart with the mic only (experimental)**: read one line so Cue learns how loud you are; quieter voices (speakers, across the table) are labelled as the other side.
- **Talk-time and filler meter**: shows how much of the conversation you've been talking, counts filler words (um, you know, 嗯, 那个), and nudges you gently.
- **Your materials, not made-up facts**: paste product docs, project notes or FAQs. The AI is told to use only your facts and numbers.
- **Search by meaning, with instant prepared answers**: with a Gemini key, every passage is embedded once (`gemini-embedding-001`, cached in your browser), and the question is embedded while it's still being asked. Paraphrased questions still find the right passage, and when it matches a Q&A in your materials the prepared answer appears immediately, before the AI responds. Keyword search is the fallback.
- **Prep → Practice → Live → Review**
  - *Prep*: generate the 8 questions you're most likely to get and your best answers.
  - *Practice*: Cue asks questions by voice; you answer by voice or text; it scores you and suggests a better answer.
  - *Live*: answers, follow-ups (expand / example / shorter / in English), cue-card mode, and points you've already covered get crossed out.
  - *Review*: what went well, what to improve, and improved answers saved back to your materials.
- **Ask Cue**: privately ask about the conversation ("what budget did they mention?").
- **Interface in English or Chinese**, with a separate setting for the answer language.
- **Follow-up after the call**: when you stop, Cue writes a summary, the other side's questions, commitments (who / what / when) and a ready-to-send follow-up email, saved to History.
- **Remember key (opt-in)**: keep your API key in this browser, encrypted with a non-extractable AES-GCM key. Uncheck to delete it.
- **History**: every session is saved in your browser and can be exported as Markdown.
- **Installable** (PWA) on desktop and phone: *Install* adds Cue as its own app window with a dock/taskbar or home-screen icon, and the app shell works offline. An always-on-top floating window is available on desktop Chrome.

## Getting started

1. Open the page in **Chrome** (desktop or Android) or Safari on iOS.
2. Paste any API key on the start screen (or **Settings → Model**). Cue detects the provider automatically (Gemini, SiliconFlow, DeepSeek, Zhipu or Qwen) by its format and by checking which service accepts it. Gemini is recommended; get a key at <https://aistudio.google.com/apikey>.
3. **Settings → Audio → Test microphone** to check permission and input level.
4. Optional: **Prep** → add your materials.
5. Press **Start listening**. With headphones on a call, tap **+ Meeting audio**, pick the meeting's tab and keep *Share tab audio* on.

## Optional: Cue extension (one-click meeting audio)

The web page can only get another tab's sound through Chrome's share picker. The small extension in [`extension/`](extension/) (also downloadable as `cue-extension.zip`) removes that step:

1. Unzip, open `chrome://extensions`, turn on **Developer mode**, click **Load unpacked** and pick the folder.
2. Open Cue and start listening. Then switch to your meeting tab and click the **Cue** icon in the toolbar.

The extension asks Chrome for a capture id for that tab that only the Cue tab can redeem, and Cue opens the audio itself. Since Chrome mutes a captured tab, Cue plays it back so you still hear the meeting. No audio passes through the extension and nothing is recorded.

## Cue Cloud (optional backend)

[`cue-server/`](cue-server/) is a small standard-library Python server so people can use Cue with an **invite code** instead of their own API key:

- `POST /v1/chat` streams answers, `POST /v1/embed` powers meaning-based search, `POST /v1/transcribe` is the fallback recognizer.
- `POST /v1/live-token` mints a **single-use, short-lived token** for Gemini Live, so the browser streams audio directly to Gemini without ever seeing the server's key.
- `POST /v1/contribute` accepts **opt-in, anonymous** training rows: hashed feature numbers plus a label, never text or audio.
- Invite codes, per-invite rate limits and daily caps, a CORS allowlist, request-size limits, and no logging of what anyone says.

Invite codes carry the server address (`cue_…@your-server.run.app`), so users paste one string and Cue detects it like any other key.

Deploy to **your own** Google Cloud project with Cloud Run (`cue-server/deploy.sh <project-id>`; easiest from Cloud Shell). The Gemini key goes into Secret Manager, never into the image. Tests: `python3 cue-server/test_server.py`.

## Desktop app (Electron)

[`cue-desktop/`](cue-desktop/) wraps the same app and adds what a browser can't do:

- **Computer audio without a share picker**: Windows uses loopback capture directly; macOS shows the native system picker once (macOS requires it for system audio).
- **Float on top**: a compact always-on-top teleprompter window.
- **Hidden from screen sharing**: content protection keeps Cue out of screen shares and recordings.

Installers for macOS (.dmg), Windows (.exe) and Linux (.AppImage) are built by GitHub Actions ([`.github/workflows/desktop.yml`](.github/workflows/desktop.yml)) and attached to each run as artifacts. Builds are unsigned for now: on macOS, right-click → Open the first time; on Windows, choose "More info → Run anyway".

## Speech recognition

| What | Engine | Notes |
|---|---|---|
| Live transcript (mic and meeting audio) | **Gemini Live streaming** (`gemini-3.5-transcribe-live`, WebSocket) | Used whenever a Gemini key or Cue Cloud is set. 16 kHz audio in 50 ms frames with a 200 ms end-of-speech window: words appear while people talk, final text about 0.03–0.25 s after they stop; a finished question sentence is acted on even before they stop. Chinese and English auto-detected. Small pieces are merged into the same speaker's line, so slow speech with pauses isn't dropped. |
| Complete transcript after the call | `gemini-3.5-flash-lite` on the recording | A compressed recording (Opus, 32 kbps, 5-minute pieces) is kept **in memory only** during the call and re-transcribed word for word when you stop, with `[mm:ss]` timestamps and speaker labels. |
| Who said what | Separate channels, or content-based labelling | With **+ Meeting audio**, your mic is "me" and the meeting tab is "them" (exact). With the mic only, `gemini-3.5-flash-lite` labels each line from the content and your materials about a second later; tap a label to fix it. |
| No key | Browser speech recognition | One language at a time; words still pending when it pauses are kept. |
| Fallback | Gemini per phrase | If streaming can't connect. |

## Privacy

- API keys live only in the page's memory unless you turn on *Remember the key*, in which case they're stored encrypted in this browser. They're never sent anywhere except the provider you chose. (The streaming connection passes the key in the WebSocket URL, which is how the Gemini Live API authenticates browsers.)
- Materials, settings and history are stored in your browser (IndexedDB). *Prep → Clear data in this browser* removes them.
- Audio is sent only to the transcription provider you configured.

## Deploying (GitHub Pages)

Put `index.html`, `manifest.webmanifest`, `sw.js`, `icon.svg` and `.nojekyll` in the repository root, then go to **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`, and save.

Microphone access requires HTTPS (GitHub Pages provides it) or `localhost`.

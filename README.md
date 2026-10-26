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

- **Live transcription of both sides**: your microphone plus the other side's audio from a meeting tab (Chrome on desktop). On phones, the microphone hears everyone in the room.
- **Automatic answers**: when the other side asks a question (with or without a question mark), an answer starts streaming right away. No hotkey needed; Space also works and uses the words heard so far.
- **Live coaching while you speak**: Cue compares what you're saying with the question and your materials, and shows *Add:* (the most important missing point) or *Fix:* (something you got wrong), about a second after you pause.
- **Talk-time meter**: shows how much of the conversation you've been talking and nudges you if you've been going for a while.
- **Your materials, not made-up facts**: paste product docs, project notes or FAQs. Matching passages appear instantly, and the AI is told to use only your facts and numbers.
- **Prep → Practice → Live → Review**
  - *Prep*: generate the 8 questions you're most likely to get and your best answers.
  - *Practice*: Cue asks questions by voice; you answer by voice or text; it scores you and suggests a better answer.
  - *Live*: answers, follow-ups (expand / example / shorter / in English), cue-card mode, and points you've already covered get crossed out.
  - *Review*: what went well, what to improve, and improved answers saved back to your materials.
- **Ask Cue**: privately ask about the conversation ("what budget did they mention?").
- **Interface in English or Chinese**, with a separate setting for the answer language.
- **History**: every session is saved in your browser and can be exported as Markdown.
- **Installable** (PWA) on desktop and phone, with an always-on-top floating window on desktop Chrome.

## Getting started

1. Open the page in **Chrome** (desktop or Android) or Safari on iOS.
2. **Settings → Model**: choose a provider and paste an API key. Gemini is recommended; get a key at <https://aistudio.google.com/apikey>.
3. **Settings → Audio → Test microphone** to check permission and input level.
4. Optional: **Prep** → add your materials.
5. Press **Start**. In an online meeting, choose the meeting's tab and turn on *Share tab audio*.

## Speech recognition

| Channel | Engine | Notes |
|---|---|---|
| The other side (meeting audio) | **Gemini Live streaming** (`gemini-3.5-transcribe-live`) | Audio is streamed continuously over a WebSocket; words appear while they talk and the final sentence about 1 s after they pause. Chinese and English are detected automatically. |
| Your microphone | Browser speech recognition (*Fast recognition*, on by default) | Words appear as you speak; one language at a time (set *Spoken language*). Turn it off or choose *mixed* to use Gemini Live instead. |
| Without a Gemini key | Browser speech recognition | Chrome versions that can recognize an audio track also transcribe the meeting tab (experimental); otherwise only the microphone works. |
| Fallback | Gemini (`gemini-3.5-flash-lite`) per phrase | Used automatically if streaming can't connect. |

Why the other side's audio needs a cloud engine: the browser's built-in recognizer has traditionally only listened to the default microphone. Audio captured from a meeting tab is raw sound data, so it has to be sent to an engine that accepts audio, such as Gemini.

## Privacy

- API keys live only in the page's memory and are never stored or sent anywhere except the provider you chose. (The streaming connection passes the key in the WebSocket URL, which is how the Gemini Live API authenticates browsers.)
- Materials, settings and history are stored in your browser (IndexedDB). *Prep → Clear data in this browser* removes them.
- Audio is sent only to the transcription provider you configured.

## Deploying (GitHub Pages)

Put `index.html`, `manifest.webmanifest`, `sw.js`, `icon.svg` and `.nojekyll` in the repository root, then go to **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`, and save.

Microphone access requires HTTPS (GitHub Pages provides it) or `localhost`.

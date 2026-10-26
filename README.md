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
- **Automatic answers**: when the other side asks a question, an answer starts streaming within about a second. No hotkey needed (Space also works).
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
| Your microphone | Browser speech recognition (*Fast recognition*, on by default) | Words appear as you speak; one language at a time (set *Spoken language*). |
| Your microphone, mixed languages | Gemini (`gemini-3.5-flash-lite`) | Handles Chinese, English and mixed speech; about 1.2–1.5 s per phrase. |
| The other side (meeting audio) | Gemini | Audio is split at natural pauses (or every ~2 s), and phrases are transcribed in parallel. |

## Privacy

- API keys live only in the page's memory and are never stored or sent anywhere except the provider you chose.
- Materials, settings and history are stored in your browser (IndexedDB). *Prep → Clear data in this browser* removes them.
- Audio is sent only to the transcription provider you configured.

## Deploying (GitHub Pages)

Put `index.html`, `manifest.webmanifest`, `sw.js`, `icon.svg` and `.nojekyll` in the repository root, then go to **Settings → Pages**, choose **Deploy from a branch**, select `main` and `/ (root)`, and save.

Microphone access requires HTTPS (GitHub Pages provides it) or `localhost`.

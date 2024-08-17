# Assistant

### Goal
Create a telegram bot with artificial intelligence that will use google calendar, todoist, gmail to control time. 

### Tools:
- [aiogram](https://aiogram.dev/) - telegram bot
- [ollama](https://ollama.com/) - local llm
- [groq](https://console.groq.com/) - free online llm (llama 3.1 70b)
- [gmail api](https://developers.google.com/gmail/api/reference/rest) - Why didn't I do the research((
- [google calendar api](https://developers.google.com/calendar/api/guides/overview) with [google calendar simple api](https://github.com/kuzmoyev/google-calendar-simple-api)
- [todoist api](https://developer.todoist.com/) with [todoist api python](https://github.com/Doist/todoist-api-python)
- [chroma](https://github.com/chroma-core/chroma) - vector database for long term memory. Maybe I'll add an online service
- [whisper](https://github.com/openai/whisper) -  There are both local implementations and via [groq](https://console.groq.com/docs/speech-text)
- [tavily](https://tavily.com/) - to connect llm to the internet
- [eleven labs](https://elevenlabs.io/) - online tts
- [Coqui.ai](https://github.com/coqui-ai/TTS) - local tts
- [pythonanywhere](https://www.pythonanywhere.com/) - as a possible host

### Todo:

- [ ] Regenerete message (llama 3.1 70b often gives nonsense)
- [ ] Hosting version (online services only)
- [ ] Add a reminder/timers. If I get too far out of the idea, I can make it just start the dialogue.
- [ ] [ElevenLabs](https://elevenlabs.io/api) setting
- [ ] Local TTS
- [ ] [WolframAlpha](https://www.wolframalpha.com/). I already have a [bot](https://github.com/Gvb3a/wolfram_telegram_bot) and it would be easy to implement, but is it necessary?
- [ ] [Character.ai](https://character.ai/). Add a mode to communicate with the characters. It will be possible then to add picture generation(SD) and stickers. But maybe I won't add it.
- [ ] Make a local calendar/todolist. I want to make it so that it would be possible to run everything locally
- [ ] Add an option to communicate not via telegram ([LiveWhisper](https://github.com/Nikorasu/LiveWhisper)).
- [ ] Add online vector bd. Solve the problem of setting it up  
- [ ] Add llm ability to change settings
- [ ] Add **deep** search using tavily. [1](https://docs.tavily.com/docs/python-sdk/tavily-search/examples)
- [ ] Add image generation (why not)
- [ ] Working with pictures

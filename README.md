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
- [vectordb](https://github.com/kagisearch/vectordb) - I may add another library and possibly online databases as well
- [whisper](https://github.com/openai/whisper) -  There are both local implementations and via [groq](https://console.groq.com/docs/speech-text)
- [pythonanywhere](https://www.pythonanywhere.com/) - as a possible host

### Todo:

- [ ] Regenerete message (llama 3.1 70b often gives nonsense)
- [ ] Add a reminder/timers. If I get too far out of the idea, I can make it just start the dialogue.
- [ ] TTS. [ElevenLabs](https://elevenlabs.io/api) or look for a local TTS, but I don't think my computer will support it, so maybe I won't.
- [ ] [WolframAlpha](https://www.wolframalpha.com/). I already have a [bot](https://github.com/Gvb3a/wolfram_telegram_bot) and it would be easy to implement, but is it necessary?
- [ ] [Character.ai](https://character.ai/). Add a mode to communicate with the characters. It will be possible then to add picture generation(SD) and stickers. But maybe I won't add it.
- [ ] Make a local calendar/todolist. I want to make it so that it would be possible to run everything locally
- [ ] Add an option to communicate not via telegram ([LiveWhisper](https://github.com/Nikorasu/LiveWhisper)).
- [ ] Search if there is a free api ChatGPT-4o, Claude 3.5 Sonnet or Perplexity.

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

- [ ] Submit chatbot assistant 'complete history of the diologue'
- [ ] Add a restriction on users and bot information
- [ ] В llm_answer сокращать историю при большом system message
- [X] Regenerete message (llama 3.1 70b often gives nonsense)
- [ ] Hosting version (online services only)
- [ ] Add a reminder(todoist)
- [ ] Add a timer
- [ ] Let the first one start the diologue
- [x] Add ElevenLabs
- [ ] [ElevenLabs](https://elevenlabs.io/api) setting
- [ ] Local TTS
- [X] Add short [WolframAlpha](https://www.wolframalpha.com/) answer
- [ ] Add full WolframAlpha answer (with step by step solution and photos)
- [ ] [Character.ai](https://character.ai/). Add a mode to communicate with the characters or use as llm. stickers.
- [ ] Make a local calendar/todolist. I want to make it so that it would be possible to run everything locally
- [ ] Add an option to communicate not via telegram ([LiveWhisper](https://github.com/Nikorasu/LiveWhisper)).
- [ ] Add online vector bd. Solve the problem of setting it up  
- [ ] Add llm ability to change settings
- [X] Add tavily
- [X] Add **deep** search using tavily
- [ ] Add image generation
- [ ] Working with pictures ([SimpleTex](https://simpletex.cn/), [OrcSpace](https://ocr.space/ocrapi), [NinjaApi](https://api-ninjas.com/api/imagetotext), [phi3 vision](https://huggingface.co/microsoft/Phi-3-vision-128k-instruct))
- [ ] Allow llm to read the mail
- [ ] [langchain](https://python.langchain.com/v0.2/docs/tutorials/agents/)?
- [ ] Enable other users (without google calendar, but still). Or create another bot based on this one

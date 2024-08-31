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

### Lanch
Download the necessary libraries (requirements.txt)\
Create this .env file
```
BOT_TOKEN=
GROQ_API_KEY= 
ADMIN_ID=
TODOIST_API=
TAVILY_API_KEY=
ELEVENLABS_API_KEY=
WOLFRAM_SIMPLE_API_KEY=
WOLFRAM_SHOW_STEPS_RESULT=
```
And fill in the api keys.\
Then you run bot.py.

*This is a temporary instruction. I'll work on it when I finish working on the bot.*

### Possibilities:
*TODO*

### Todo:

- [ ] Local llm wia hugging face
- [ ] Add a restriction on users and bot information
- [X] Regenerete message (llama 3.1 70b often gives nonsense)
- [ ] Hosting version (online services only)
- [ ] Add a reminder(todoist)
- [ ] Add a timer
- [ ] Let the first one start the diologue
- [X] Add full [WolframAlpha](https://www.wolframalpha.com/) answer (photos)
- [ ] [Character.ai](https://character.ai/). Add a mode to communicate with the characters or use as llm. stickers.
- [ ] Make a local calendar/todolist. I want to make it so that it would be possible to run everything locally
- [ ] Add an option to communicate not via telegram ([LiveWhisper](https://github.com/Nikorasu/LiveWhisper)).
- [ ] Add the ability to work with documents (vector datebase)
- [ ] Add online vector bd. Solve the problem of setting it up
- [X] Add tavily
- [X] Add deep search using tavily
- [X] Add image generation
- [ ] Working with pictures ([SimpleTex](https://simpletex.cn/), [OrcSpace](https://ocr.space/ocrapi), [NinjaApi](https://api-ninjas.com/api/imagetotext), [phi3 vision](https://huggingface.co/microsoft/Phi-3-vision-128k-instruct)). Maybe in google colab place the model and make an api
- [ ] Allow llm to read the mail
- [X] [langchain](https://python.langchain.com/v0.2/docs/tutorials/agents/)?
- [ ] Make a customization: use langchain ot not
- [ ] Enable other users (without google calendar, but still)
- [ ] If I'm going to do other people's access, I need to catch error.
- [ ] Add a temporary message. It may display additional information.
- [x] Split llm_answer into 4-3 functions. You can output the information in a temporary message
- [ ] Add the ability to make multiple posts in Wolfram (separator - ;). Asynchronously
- [ ] Add [Code Interpreting](https://e2b.dev/P)
- [ ] Rebuild a complete vector datebase
- [ ] Figure out the timeline for the calendar, add visualizations, and see how to give access to other users

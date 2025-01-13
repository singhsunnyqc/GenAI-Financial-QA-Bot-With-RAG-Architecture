The solution is self-contained where you would need to run only one file fin_bot.py

- Start by installing the dependencies by running pip install -r requirements.txt
- Runt the RAG application from the terminal by running 
	python3 fin_bot.py OPENAI_API_KEY THE_QUESTION

- Works with Python3.13.1
- Add your own OpenAPI key in env file
- run `streamlint run src/app.py` to start the bot


## Responsible AI Features

- Explainibility (Every bot response has a link to source)
- Prevent hallucinations using system prompt
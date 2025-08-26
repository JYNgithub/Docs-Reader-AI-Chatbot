# DocsReader

Not the 1000th PDF or document chatbot.  
**DocsReader** is a chatbot designed to be your learning partner for up to 15 Python libraries, using **official documentation** as its source.  

- Can it build your whole project with one prompt? **No**  
- Can it help you learn new tools with accurate syntax and information? **Yes**  

---

## How It Works

Official documentations of Python libraries are scraped as vector embeddings to be used in Retrieval-Augmented Generation (RAG) for the AI chatbot. Meaning, the chatbot receives accurate information to prevent hallucination. Another thing with latest Python libraries are that changes are frequent, meaning that mainstream chatbots like ChatGPT are prone to giving outdated and deprecated code suggestions due to their slow updates. This chatbot solves this problems by directly scraping official documentation, without having to rely on inconsistent Web Search feature by other coding assistants. 

---

## Usage

You may run the app via Docker or local deployment.

### via Docker

1. Clone the repo
```bash
git clone https://github.com/JYNgithub/Docs-Reader-AI-Chatbot
```

2. Install/Launch Docker 

3. Pull the pre-built image
```bash
docker-compose pull
```

4. Run the container
```bash
docker-compose up
```

5. Access the web app at http://localhost:8501/

### via Local Deployment

1. Clone the repo
```bash
git clone https://github.com/JYNgithub/Docs-Reader-AI-Chatbot
```

2. Create and activate a venv in the project folder
```bash
python -m venv .venv
call .venv/Scripts/activate
```

or if you are on Linux/macOS:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Run the app
```bash
streamlit run app.py
```

5. Access the web app at http://localhost:8501/

---

## Supported Libraries

1. Chroma
2. Pillow
3. PySpark
4. LangGraph
5. LangChain
6. Transformers
7. Tokenizers
8. Gradio
9. FastAPI
10. Psycopg2
11. Psycopg3
12. Redis
13. SQLAlchemy
14. DataBricks-SDK
15. NiceGUI

---

## Limitations

As this is a hobby project, it has some limitations:
- Limited number of libraries supported
- Limited scalability
- Inconsistent updates of scraped documentation until a CI/CD process is established



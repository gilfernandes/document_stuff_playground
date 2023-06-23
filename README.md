# Document Chain Playground

This repository shows how you can create a small Python based application that reads some documents, extracts OpenAI embeddings 
and uses these for question and answers against ChatGPT.

The documents we used for testing were CVs against which we asked the following questions:

"What is the name of the job candidate?",
"What are the specialities of this candidate?",
"Please extract all hyperlinks.",
"How many years of experience does this candidate have as a mobile developer?"

```bash
conda create --name langchain_fastapi python=3.10
conda activate langchain_fastapi
conda install -c conda-forge mamba
mamba install openai
mamba install langchain
mamba install fastapi
pip install pdfplumber
pip install chromadb
pip install tiktoken
mamba install docx2txt
```
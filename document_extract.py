import sys
from pathlib import Path
from typing import List
from langchain.docstore.document import Document
from langchain.document_loaders import PDFPlumberLoader, Docx2txtLoader
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.chains import RetrievalQA
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

class Config(): 
    model = 'gpt-3.5-turbo-16k'
    # model = 'gpt-4'
    llm = ChatOpenAI(model=model, temperature=0)
    embeddings = OpenAIEmbeddings()
    chunk_size = 2000
    chroma_persist_directory = 'chroma_store'

cfg = Config()

questions = [
    "What is the name of the job candidate?",
    "What are the specialities of this candidate?",
    "Please extract all hyperlinks.",
    "How many years of experience does this candidate have as a mobile developer?",
    # "Did you find any spelling mistakes in the text? If so, can you point them to me?"
]

@dataclass
class CandidateInfo():
    candidate_file: str
    questions: list[(str, str)]


def process_document_path(doc_path) -> Chroma:
    if not isinstance(doc_path, Path):
        doc_path = Path(doc_path)
    if not doc_path.exists():
        print(f"The document ({doc_path}) does not exist. Please check")
    else:
        print(f"Processing {doc_path}")
        loader = (PDFPlumberLoader(str(doc_path)) if doc_path.suffix == ".pdf"
                  else Docx2txtLoader(str(doc_path)))
        doc_list: List[Document] = loader.load()
        print(f"Extracted documents: {len(doc_list)}")
        for i, doc in enumerate(doc_list):
            i += 1
            if len(doc.page_content) == 0:
                print(f"Document has empty page: {i}")
            else:
                print(f"Page {i} length: {len(doc.page_content)}")
        text_splitter = CharacterTextSplitter(chunk_size=cfg.chunk_size, chunk_overlap=0)
        texts = text_splitter.split_documents(doc_list)

        return extract_embeddings(texts, doc_path)
    

def extract_embeddings(texts: List[Document], doc_path: Path) -> Chroma:
    """
    Either saves the Chroma embeddings locally or reads them from disk, in case they exist.

    """
    embedding_dir = f"{cfg.chroma_persist_directory}/{doc_path.stem}"
    if Path(embedding_dir).exists():
        return Chroma(persist_directory=embedding_dir, embedding_function=cfg.embeddings)
    try:
        docsearch = Chroma.from_documents(texts, cfg.embeddings, persist_directory=embedding_dir)
        docsearch.persist()
    except Exception as e:
        print(f"Failed to process {doc_path}: {str(e)}")
        return None
    return docsearch
        
    

def extract_candidate_infos(doc_folder: Path) -> list[CandidateInfo]:
    if not doc_folder.exists():
        print(f"Candidate folder {doc_folder} does not exist!")
        return []
    candidate_list: list[CandidateInfo] = []
    extensions: list[str] = ['**/*.pdf', '**/*.docx']
    for extension in extensions:
        for doc in doc_folder.rglob(extension):
            docsearch = process_document_path(doc)
            print(f"Processed {doc}")
            if docsearch is not None:
                qa = RetrievalQA.from_chain_type(llm=cfg.llm, chain_type="stuff", retriever=docsearch.as_retriever())
                question_list = []
                for question in questions:
                    question_list.append((question, qa.run(question)))
                candidate_list.append(CandidateInfo(candidate_file=doc.stem, questions=question_list))
            else:
                print(f"Could not retrieve content from {doc}")
    return candidate_list


def render_candidate_infos(candidate_infos: list[CandidateInfo]) -> str:
    html = ""
    for candidate_info in candidate_infos:
        qa_html = ""
        for question, answer in candidate_info.questions:
            qa_html += f"""
<h5 class="card-title">{question}</h5>
<p class="card-text"><pre style="background-color: #f6f8fa; padding: 1em">{answer}</pre></p>
"""
        html += f"""
<div class="card">
  <div class="card-header" style="cursor: pointer">
    {candidate_info.candidate_file}
  </div>
  <div class="card-body mb-3">
    {qa_html}
  </div>
</div>
"""
    return html
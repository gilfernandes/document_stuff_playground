from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from document_extract import CandidateInfo, extract_candidate_infos, render_candidate_infos

import uvicorn
import threading
import logging
import time

from pathlib import Path
from datetime import datetime

def setup_fastapi():
    app = FastAPI()
    origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app

class CandidateCache():
    candidate_info_html = "<p>Processing, please wait ...</p>"

candidate_cache = CandidateCache()

SLEEP_TIME = 60 * 10

class BackgroundTasks(threading.Thread):

    """
    Processes documents and query Chat GPT in the background.
    """

    def __init__(self, candidate_cache: CandidateCache, sleep_time = SLEEP_TIME):
        super().__init__()
        self.candidate_cache, self.sleep_time = candidate_cache, sleep_time
        self.data_cache = sleep_time

    def run(self, *args, **kwargs):
        while True:
            candidate_infos: list[CandidateInfo] = extract_candidate_infos(Path("."))
            self.candidate_cache.candidate_info_html = render_candidate_infos(candidate_infos)
            logging.info('Updated doc analysis')
            time.sleep(self.sleep_time)

t = BackgroundTasks(candidate_cache)
t.start()

app = setup_fastapi()

@app.get("/hello")
async def hello():
    return {
        "hello": "there"
    }

@app.get("/candidates.html", response_class=HTMLResponse)
async def hello_html():

    def generate_timestamp():
        # Get the current date and time
        now = datetime.now()

        # Get the weekday, day, month, year, and time in English
        weekday = now.strftime("%A")
        day = now.strftime("%d")
        month = now.strftime("%B")
        year = now.strftime("%Y")
        time = now.strftime("%H:%M:%S")

        # Create the timestamp string
        timestamp = f"{weekday}, {day} {month} {year} {time}"

        return timestamp

    return f"""
<html>
    <head>
        <meta charset="UTF-8" />
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM" crossorigin="anonymous">
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js" integrity="sha384-geWF76RCwLtnZ8qwWowPQNguL3RmwHVBC9FhGdlKrxdiJJigb/j/68SIy3Te4Bkz" crossorigin="anonymous"></script>
        <style>
            pre {{
                white-space: pre-wrap;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Candidate Information</h1>
            <h4>{generate_timestamp()}</h4>
            <div class="row">
                <div class="col-12 mb-3" style="text-align: right">
                    <button type="button" class="btn btn-light">Toggle Cards</button>
                </div>
            </div>
            {candidate_cache.candidate_info_html}
        </div>
        <script>
            [...document.querySelectorAll(".card-header")]
                .forEach(e => e.addEventListener("click", () => e.parentNode.querySelector(".card-body").classList.toggle('d-none')))
            function toggleCards() {{
                [...document.querySelectorAll(".card-body")].forEach(e => e.classList.toggle('d-none'))
            }}
            document.querySelector("button").addEventListener("click", toggleCards)
        </script>
    </body>
</html>
"""

if __name__ == '__main__':
    print("Fast API setup")    
    uvicorn.run(app, host="0.0.0.0", port=8000)
        
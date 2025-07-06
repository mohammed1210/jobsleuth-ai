# FastAPI main entry point

from fastapi import FastAPI

app = FastAPI()

@app.get('/health')
def health_check():
    return {'status': 'ok'}

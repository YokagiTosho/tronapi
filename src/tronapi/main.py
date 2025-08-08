from fastapi import FastAPI
from tronpy import Tron

app = FastAPI()

tron = Tron()

@app.get("/get_last_records/")
def get_last_records(page: int = 1):
    limit = 10
    return {'offset': (page-1)*limit, 'limit': limit}


@app.post("/wallet/")
def wallet_information(address: str):
    return {'address': address}

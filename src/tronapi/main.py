import os

from fastapi import FastAPI

from tronpy import AsyncTron
from tronpy.providers import AsyncHTTPProvider

from typing import Optional

API_KEY: Optional[str] = os.getenv("API_KEY", None)
if API_KEY is None:
    print("API KEY is not specified")
    exit(1)

app = FastAPI()

tron_provider = AsyncHTTPProvider(api_key=API_KEY)


@app.get("/get_last_records/")
async def get_last_records(page: int = 1):
    limit = 10
    return {"offset": (page - 1) * limit, "limit": limit}


@app.post("/wallet/")
async def wallet_information(address: str):
    async with AsyncTron(tron_provider) as client:
        energy = await client.get_energy(address)
        bandwidth = await client.get_bandwidth(address)
        balance = await client.get_account_balance(address)

        return {
            "address": address,
            "account_info": {
                "energy": energy,
                "bandwidth": bandwidth,
                "trx balance": balance,
            },
        }

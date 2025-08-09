import httpx
import os
import time

def test_endpoint():
    tronapi_addr = os.getenv("TRONAPI_ADDR")

    if tronapi_addr is None:
        raise ValueError("TRONAPI_ADDR is not specified in environment variables")

    # wait unit fastapi is fully launched
    time.sleep(2)

    address = "fwaifawigawgawgawj124"
    resp = httpx.post(f"http://{tronapi_addr}/wallet/?address={address}")
    assert resp.status_code == 400

    address = "TNebqVps2RUEfv8zxfXcYJtNoXz7Tp3vpN"
    resp = httpx.post(f"http://{tronapi_addr}/wallet/?address={address}")
    assert resp.status_code == 200
    assert resp.json()['address'] == address

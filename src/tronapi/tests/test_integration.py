import httpx
import os
import time

def test_endpoint():
    tronapi_addr = os.getenv("TRONAPI_ADDR")

    assert tronapi_addr is not None

    # wait unit fastapi is fully launched
    time.sleep(2)

    address = "fwaifawigawgawgawj124"
    resp = httpx.post(f"http://{tronapi_addr}/wallet/?address={address}")
    assert resp.status_code == 400

    address = "TNebqVps2RUEfv8zxfXcYJtNoXz7Tp3vpN"
    resp = httpx.post(f"http://{tronapi_addr}/wallet/?address={address}")
    assert resp.status_code == 200
    assert resp.json()['address'] == address

import os
import requests
from typing import Optional, Dict, Any


class ZeroXClient:
    def __init__(self, api_key: str, base_url: Optional[str] = None):
        self.api_key = api_key
        self.base_url = base_url or "https://api.0x.org"
        self.headers = {
            "0x-api-key": self.api_key,
            "0x-version": "v2",
        }

    def get_permit2_quote(
        self,
        chain_id: int,
        taker: str,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
        slippage_bps: int = 100,
        fee_recipient: Optional[str] = None,
        buy_token_percentage_fee: float = 0.0,
    ) -> Dict[str, Any]:
        params = {
            "chainId": str(chain_id),
            "taker": taker,
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmount": sell_amount,
            "slippageBps": str(slippage_bps),
        }
        if fee_recipient and buy_token_percentage_fee > 0:
            params["feeRecipient"] = fee_recipient
            params["buyTokenPercentageFee"] = str(buy_token_percentage_fee)

        url = f"{self.base_url}/swap/permit2/quote"
        r = requests.get(url, params=params, headers=self.headers, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"0x quote failed: {r.status_code} {r.text}")
        return r.json()

    def get_permit2_price(
        self,
        chain_id: int,
        taker: str,
        sell_token: str,
        buy_token: str,
        sell_amount: str,
    ) -> Dict[str, Any]:
        params = {
            "chainId": str(chain_id),
            "taker": taker,
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmount": sell_amount,
        }
        url = f"{self.base_url}/swap/permit2/price"
        r = requests.get(url, params=params, headers=self.headers, timeout=30)
        if r.status_code != 200:
            raise RuntimeError(f"0x price failed: {r.status_code} {r.text}")
        return r.json()
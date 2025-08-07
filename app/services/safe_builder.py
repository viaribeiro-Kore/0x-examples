from typing import List, Dict, Any
import time


def build_tx_builder_json(
    chain_id: int,
    safe_address: str,
    transactions: List[Dict[str, str]],
    name: str = "Batch",
    description: str = "",
) -> Dict[str, Any]:
    now_ms = int(time.time() * 1000)
    return {
        "version": "1.0",
        "chainId": str(chain_id),
        "createdAt": now_ms,
        "meta": {
            "name": name,
            "description": description,
            "txBuilderVersion": "1.0",
            "createdFromSafeAddress": safe_address,
            "createdFromOwnerAddress": None,
        },
        "transactions": [
            {
                "to": tx["to"],
                "value": str(tx.get("value", "0")),
                "data": tx.get("data", "0x"),
                # Optional fields supported by the builder
                "contractMethod": None,
                "contractInputsValues": None,
            }
            for tx in transactions
        ],
    }
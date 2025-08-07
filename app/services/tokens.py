from typing import Dict, Optional
from decimal import Decimal, ROUND_DOWN

# Minimal curated lists for demo. Extend as needed.
# Addresses in checksum or lower are fine; 0x API accepts either.
TOKEN_LISTS: Dict[int, list] = {
    1: [  # Ethereum Mainnet
        {"symbol": "ETH", "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", "decimals": 18},
        {"symbol": "WETH", "address": "0xC02aaA39b223FE8D0a0e5C4F27eAD9083C756Cc2", "decimals": 18},
        {"symbol": "USDC", "address": "0xA0b86991c6218b36c1d19d4a2e9eb0ce3606eb48", "decimals": 6},
        {"symbol": "USDT", "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7", "decimals": 6},
        {"symbol": "DAI",  "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F", "decimals": 18},
    ],
    8453: [  # Base
        {"symbol": "ETH", "address": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE", "decimals": 18},
        {"symbol": "USDC", "address": "0x833589fCD6EDB6E08f4c7c32D4f71B54BDA02913", "decimals": 6},
        {"symbol": "DAI",  "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb", "decimals": 18},
        {"symbol": "USDbC","address": "0x2eBc0dB28A091BbD39f8Cdd1dD174a5272388d0A", "decimals": 6},
        {"symbol": "WETH", "address": "0x4200000000000000000000000000000000000006", "decimals": 18},
    ],
}


def get_token_by_symbol_or_address(chain_id: int, key: str) -> Optional[dict]:
    tokens = TOKEN_LISTS.get(chain_id, [])
    key_lower = key.lower()
    for t in tokens:
        if t["symbol"].lower() == key_lower or t["address"].lower() == key_lower:
            return t
    return None


def to_base_units(amount_human: str, decimals: int) -> str:
    q = Decimal(amount_human)
    scale = Decimal(10) ** decimals
    return str((q * scale).to_integral_exact(rounding=ROUND_DOWN))


def from_base_units(amount_raw: str, decimals: int) -> str:
    q = Decimal(amount_raw)
    scale = Decimal(10) ** decimals
    return format(q / scale, 'f')
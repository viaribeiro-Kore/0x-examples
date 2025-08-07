from web3 import Web3
from typing import Optional
from eth_abi import encode as abi_encode


ERC20_ABI = [
    {
        "constant": True,
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"},
        ],
        "name": "allowance",
        "outputs": [{"name": "remaining", "type": "uint256"}],
        "type": "function",
    },
    {
        "constant": False,
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "value", "type": "uint256"},
        ],
        "name": "approve",
        "outputs": [{"name": "", "type": "bool"}],
        "type": "function",
    },
]


def build_erc20_approve_calldata(spender: str, amount: int = (2**256 - 1)) -> str:
    # bytes4(keccak256("approve(address,uint256)")) = 0x095ea7b3
    method_selector = bytes.fromhex("095ea7b3")
    encoded = abi_encode(["address", "uint256"], [spender, amount])
    return "0x" + (method_selector + encoded).hex()


class AllowanceChecker:
    # Uniswap Permit2 canonical address
    PERMIT2_ADDRESS = "0x000000000022D473030F116dDEE9F6B43aC78BA3"
    NATIVE_TOKEN_ZERO = "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee"

    def __init__(self, rpc_url: str):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 20}))
        if not self.w3.is_connected():
            raise RuntimeError("Failed to connect to RPC")

    def get_allowance(self, token_address: str, owner: str, spender: str) -> str:
        if token_address.lower() == self.NATIVE_TOKEN_ZERO:
            return "0"
        contract = self.w3.eth.contract(address=Web3.to_checksum_address(token_address), abi=ERC20_ABI)
        value = contract.functions.allowance(Web3.to_checksum_address(owner), Web3.to_checksum_address(spender)).call()
        return str(value)
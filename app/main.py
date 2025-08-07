from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import os
import time

from services.tokens import TOKEN_LISTS, get_token_by_symbol_or_address, to_base_units, from_base_units
from services.zerox import ZeroXClient
from services.approvals import AllowanceChecker, build_erc20_approve_calldata
from services.safe_builder import build_tx_builder_json


class SwapItem(BaseModel):
    sellToken: str
    buyToken: str
    amount: str  # human units string
    feeBps: int = 0
    feeRecipient: Optional[str] = None
    slippageBps: int = 100  # default 1%


class BuildBatchRequest(BaseModel):
    chainId: int = Field(..., description="EVM chain ID (e.g., 1 for Ethereum)")
    safeAddress: str
    swaps: List[SwapItem]
    rpcUrl: Optional[str] = None


class BuildBatchResponse(BaseModel):
    txBuilderJson: Dict[str, Any]
    approvalsAdded: List[Dict[str, Any]]
    swapTransactions: List[Dict[str, Any]]
    gasEstimate: Optional[int] = None
    warnings: List[str] = []


app = FastAPI(title="Safe Rebalance Batch Builder", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (frontend)
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")


@app.get("/api/tokens")
async def list_tokens(chainId: int = 1):
    tokens = TOKEN_LISTS.get(chainId)
    if not tokens:
        raise HTTPException(status_code=400, detail=f"Unsupported chainId: {chainId}")
    return {"chainId": chainId, "tokens": tokens}


@app.post("/api/build-batch", response_model=BuildBatchResponse)
async def build_batch(req: BuildBatchRequest):
    if not req.swaps:
        raise HTTPException(status_code=400, detail="No swaps provided")

    # Setup helpers
    zerox_api_key = os.environ.get("ZEROX_API_KEY")
    if not zerox_api_key:
        raise HTTPException(status_code=500, detail="ZEROX_API_KEY not configured")
    zxc = ZeroXClient(api_key=zerox_api_key)

    rpc_url = req.rpcUrl or os.environ.get("RPC_URL")
    if not rpc_url:
        raise HTTPException(status_code=500, detail="RPC_URL not provided and not set in env")
    allowance = AllowanceChecker(rpc_url)

    transactions: List[Dict[str, Any]] = []
    approvals_added: List[Dict[str, Any]] = []
    swap_txs: List[Dict[str, Any]] = []
    warnings: List[str] = []
    gas_total = 0

    for swap in req.swaps:
        sell_token = get_token_by_symbol_or_address(req.chainId, swap.sellToken)
        buy_token = get_token_by_symbol_or_address(req.chainId, swap.buyToken)
        if not sell_token or not buy_token:
            raise HTTPException(status_code=400, detail=f"Unknown token in swap: {swap.sellToken} -> {swap.buyToken}")

        sell_amount_raw = to_base_units(swap.amount, sell_token["decimals"])  # string

        # 1) Check Permit2 allowance (Permit2 address is static across chains)
        permit2_address = allowance.PERMIT2_ADDRESS
        if sell_token["address"] != allowance.NATIVE_TOKEN_ZERO:
            current_allowance = allowance.get_allowance(
                token_address=sell_token["address"], owner=req.safeAddress, spender=permit2_address
            )
            needs_approval = int(current_allowance, 10) < int(sell_amount_raw, 10)
            if needs_approval:
                approve_data = build_erc20_approve_calldata(permit2_address)
                transactions.append({
                    "to": sell_token["address"],
                    "value": "0",
                    "data": approve_data,
                })
                approvals_added.append({
                    "token": sell_token["symbol"],
                    "spender": permit2_address,
                    "currentAllowance": current_allowance,
                })
                gas_total += 60000  # coarse estimate for approve
        else:
            warnings.append(f"Skipping allowance for native token {sell_token['symbol']}")

        # 2) Get 0x quote (Permit2 path). Include fee & slippage.
        fee_recipient = swap.feeRecipient or req.safeAddress
        buy_token_percentage_fee = max(0.0, min(1.0, (swap.feeBps or 0) / 10000.0))

        quote = zxc.get_permit2_quote(
            chain_id=req.chainId,
            taker=req.safeAddress,
            sell_token=sell_token["address"],
            buy_token=buy_token["address"],
            sell_amount=sell_amount_raw,
            slippage_bps=swap.slippageBps,
            fee_recipient=fee_recipient,
            buy_token_percentage_fee=buy_token_percentage_fee,
        )
        if not quote.get("transaction"):
            raise HTTPException(status_code=500, detail=f"0x quote missing transaction for {sell_token['symbol']} -> {buy_token['symbol']}")

        tx = quote["transaction"]
        # Ensure value is string
        tx_value = str(tx.get("value") or 0)
        transactions.append({
            "to": tx["to"],
            "value": tx_value,
            "data": tx["data"],
        })
        swap_txs.append({
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmountRaw": sell_amount_raw,
            "minBuyAmount": quote.get("minBuyAmount"),
            "route": quote.get("route"),
            "fees": quote.get("fees"),
            "issues": quote.get("issues"),
        })
        try:
            gas_total += int(tx.get("gas") or 0)
        except Exception:
            pass

        # Optional: warn on allowances reported by 0x
        issues = quote.get("issues", {})
        if issues.get("allowance") and issues["allowance"].get("actual") == "0":
            warnings.append(f"0x indicates allowance may be required for {sell_token['symbol']}")

    # 3) Build Safe Transaction Builder JSON
    batch_json = build_tx_builder_json(
        chain_id=req.chainId,
        safe_address=req.safeAddress,
        transactions=transactions,
        name="Rebalance Batch",
        description="Batch of approvals (if needed) + swaps via 0x",
    )

    return BuildBatchResponse(
        txBuilderJson=batch_json,
        approvalsAdded=approvals_added,
        swapTransactions=swap_txs,
        gasEstimate=gas_total or None,
        warnings=warnings,
    )


@app.get("/api/download-batch")
async def download_batch(chainId: int, safeAddress: str, filename: Optional[str] = None):
    # This endpoint expects the client to POST to /api/build-batch first in practice. Here we keep only POST-based download in UI.
    return JSONResponse({"error": "Use POST /api/build-batch and download on the client"}, status_code=400)
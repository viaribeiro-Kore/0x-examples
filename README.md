Safe Rebalance Batch Builder (FastAPI + Minimal Frontend)

What it does
- Build a Safe Transaction Builder JSON batch of ERC-20 approvals (Permit2) and 0x Swap v2 Permit2 swaps
- Advisor can add multiple swaps and download a single batch JSON for the client to approve in Safe{Wallet}
- Auto-check ERC-20 allowances to Permit2; auto-includes approve() if insufficient
- Simple UI handles token decimals, default fee bps, slippage, and draft save/load

Requirements
- Python 3.10+
- A 0x API key (Dashboard)
- RPC URL for the selected chain (e.g., Ethereum mainnet)

Quick start
1) Configure env
Create `.env`:

ZEROX_API_KEY=your_0x_api_key
RPC_URL=https://mainnet.infura.io/v3/your_key

2) Install

pip install -r requirements.txt

3) Run dev server

uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

4) Open UI
- Navigate to http://localhost:8000

Using the tool
- Enter Chain, Safe address, optional RPC URL override
- Set default fee bps (affiliate) and slippage bps
- Add swaps: sell token, buy token, human amount
- Build Batch: backend fetches 0x quotes and checks allowances to Permit2
- Download for Safe Wallet: saves a `safe-batch.json` compatible with the Safe Transaction Builder import

Notes
- Permit2: We use ERC20 approve to Permit2 (0x000000000022D473030F116dDEE9F6B43aC78BA3) when allowance is insufficient; this avoids needing an EIP-712 Permit2 signature in calldata
- 0x Fees: The UI passes `feeRecipient` and `buyTokenPercentageFee` to 0x; fee is taken from the buy token
- Gas estimate: Sum of 0x `transaction.gas` plus ~60k per approval (coarse)
- Supported tokens: a small curated list for ETH/Mainnet and Base; extend `app/services/tokens.py` as needed
- Batch format: standard Safe Transaction Builder JSON with minimal fields `version, chainId, createdAt, meta, transactions`

Production
- Behind a reverse proxy, add rate limiting and input validation
- Add more chains and tokens; optionally fetch Safe token list from Safe APIs
- Secure CORS and set a server-side allowlist if exposing publicly

FAQ
- Does this require 0x Permit2 signature appended to calldata? No, we rely on on-chain allowances to Permit2 which 0x supports, so no EIP-712 signature is necessary in the calldata.
- Can I adjust fee per swap? Yes, edit in the table after adding.
- Can I save drafts? Yes, use Save/Load Draft (localStorage).

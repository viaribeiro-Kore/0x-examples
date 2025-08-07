let state = {
  chainId: 1,
  safeAddress: "",
  rpcUrl: "",
  swaps: [],
  tokens: [],
};

async function fetchTokens(chainId) {
  const res = await fetch(`/api/tokens?chainId=${chainId}`);
  if (!res.ok) throw new Error("Failed to load tokens");
  const data = await res.json();
  state.tokens = data.tokens;
  const sellSel = document.getElementById("sellToken");
  const buySel = document.getElementById("buyToken");
  sellSel.innerHTML = "";
  buySel.innerHTML = "";
  state.tokens.forEach(t => {
    const o1 = document.createElement("option"); o1.value = t.symbol; o1.textContent = `${t.symbol}`; sellSel.appendChild(o1);
    const o2 = document.createElement("option"); o2.value = t.symbol; o2.textContent = `${t.symbol}`; buySel.appendChild(o2);
  });
}

function renderSwaps() {
  const tbody = document.querySelector("#swapsTable tbody");
  tbody.innerHTML = "";
  state.swaps.forEach((s, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `<td>${s.sellToken}</td><td>${s.buyToken}</td><td>${s.amount}</td>`+
      `<td><input data-idx="${i}" data-k="feeBps" type="number" min="0" max="10000" value="${s.feeBps || 0}"/></td>`+
      `<td><input data-idx="${i}" data-k="slippageBps" type="number" min="0" max="10000" value="${s.slippageBps || 100}"/></td>`+
      `<td><button data-del="${i}">Remove</button></td>`;
    tbody.appendChild(tr);
  });
}

function attachTableHandlers() {
  document.querySelector("#swapsTable tbody").addEventListener("change", (e) => {
    const idx = e.target.getAttribute("data-idx");
    const k = e.target.getAttribute("data-k");
    if (idx !== null && k) {
      state.swaps[idx][k] = Number(e.target.value);
    }
  });
  document.querySelector("#swapsTable tbody").addEventListener("click", (e) => {
    const del = e.target.getAttribute("data-del");
    if (del !== null) {
      state.swaps.splice(Number(del), 1);
      renderSwaps();
    }
  });
}

function saveDraft() {
  const draft = {
    chainId: Number(document.getElementById("chainId").value),
    safeAddress: document.getElementById("safeAddress").value,
    rpcUrl: document.getElementById("rpcUrl").value,
    feeRecipient: document.getElementById("feeRecipient").value,
    feeBps: Number(document.getElementById("feeBps").value || 0),
    slippageBps: Number(document.getElementById("slippageBps").value || 100),
    swaps: state.swaps,
  };
  localStorage.setItem("rebalanceDraft", JSON.stringify(draft));
  alert("Draft saved");
}

function loadDraft() {
  const raw = localStorage.getItem("rebalanceDraft");
  if (!raw) return alert("No draft found");
  const d = JSON.parse(raw);
  document.getElementById("chainId").value = d.chainId;
  document.getElementById("safeAddress").value = d.safeAddress;
  document.getElementById("rpcUrl").value = d.rpcUrl || "";
  document.getElementById("feeRecipient").value = d.feeRecipient || "";
  document.getElementById("feeBps").value = d.feeBps || 0;
  document.getElementById("slippageBps").value = d.slippageBps || 100;
  state.chainId = d.chainId;
  state.safeAddress = d.safeAddress;
  state.rpcUrl = d.rpcUrl;
  state.swaps = d.swaps || [];
  fetchTokens(state.chainId).then(renderSwaps);
}

async function buildBatch() {
  const chainId = Number(document.getElementById("chainId").value);
  const safeAddress = document.getElementById("safeAddress").value.trim();
  const rpcUrl = document.getElementById("rpcUrl").value.trim();
  const feeRecipientDefault = document.getElementById("feeRecipient").value.trim();
  const feeBpsDefault = Number(document.getElementById("feeBps").value || 0);
  const slippageBpsDefault = Number(document.getElementById("slippageBps").value || 100);

  if (!safeAddress) return alert("Enter Safe address");
  if (!state.swaps.length) return alert("Add at least one swap");

  const swaps = state.swaps.map(s => ({
    sellToken: s.sellToken,
    buyToken: s.buyToken,
    amount: s.amount,
    feeBps: (s.feeBps ?? feeBpsDefault),
    feeRecipient: feeRecipientDefault || undefined,
    slippageBps: (s.slippageBps ?? slippageBpsDefault),
  }));

  const payload = { chainId, safeAddress, rpcUrl: rpcUrl || undefined, swaps };
  const res = await fetch("/api/build-batch", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const out = document.getElementById("result");
  const warn = document.getElementById("warnings");
  if (!res.ok) {
    const txt = await res.text();
    out.textContent = txt;
    warn.textContent = "";
    return;
  }
  const data = await res.json();
  window._lastBatch = data.txBuilderJson;
  out.textContent = JSON.stringify(data, null, 2);
  warn.textContent = (data.warnings || []).join("\n");
  document.getElementById("download").disabled = false;
}

function downloadBatch() {
  const json = window._lastBatch;
  if (!json) return alert("Nothing to download");
  const blob = new Blob([JSON.stringify(json, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = "safe-batch.json"; a.click();
  URL.revokeObjectURL(url);
}

function addSwap() {
  const sell = document.getElementById("sellToken").value;
  const buy = document.getElementById("buyToken").value;
  const amt = document.getElementById("amount").value.trim();
  if (!amt || Number(amt) <= 0) return alert("Enter amount");
  if (sell === buy) return alert("Sell and Buy token must differ");
  state.swaps.push({ sellToken: sell, buyToken: buy, amount: amt, feeBps: Number(document.getElementById("feeBps").value || 0), slippageBps: Number(document.getElementById("slippageBps").value || 100) });
  renderSwaps();
}

function attach() {
  document.getElementById("chainId").addEventListener("change", (e) => {
    state.chainId = Number(e.target.value);
    fetchTokens(state.chainId);
  });
  document.getElementById("addSwap").addEventListener("click", addSwap);
  document.getElementById("build").addEventListener("click", buildBatch);
  document.getElementById("download").addEventListener("click", downloadBatch);
  document.getElementById("saveDraft").addEventListener("click", saveDraft);
  document.getElementById("loadDraft").addEventListener("click", loadDraft);
  attachTableHandlers();
}

window.addEventListener("DOMContentLoaded", async () => {
  await fetchTokens(state.chainId);
  attach();
});
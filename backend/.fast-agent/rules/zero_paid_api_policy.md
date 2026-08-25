# Policy: Zero-Paid API Architecture & Multi-Key Auto-Rotation

## Core Mandate:
1. **Zero-Paid API Budget**: IconEdge Technologies operates on a 100% free multi-key architecture. We do NOT pay for API subscriptions or tokens.
2. **Silent Multi-Key Failover**:
   - Whenever any API key hits a rate limit (429), credit depletion (402), or model error (404/400), the internal `MultiModelRouter` MUST automatically apply cooldown and cascade to the next available key or provider in the pool:
     $$\text{Google Gemini} \longrightarrow \text{OpenRouter Free Pool} \longrightarrow \text{Groq} \longrightarrow \text{Cerebras} \longrightarrow \text{DeepSeek}$$
3. **Zero Errors to Mr. Owen**:
   - Never surface 429, 402, or "credit limit exceeded" errors to Mr. Owen. Failovers must execute silently in the background.
4. **Key Pool Maintenance**:
   - Multi-key rotation supports additional keys in `.env` (e.g. `GEMINI_API_KEY_2`, `GROQ_API_KEY_2`, `DEEPSEEK_API_KEY_2`).

# --- CONFIGURAÇÕES ---
TARGET_ENDPOINT = "https://api.iaedu.pt/agent-chat/api/v1/agent/xxxxxxxxxxxxxxxxxxxxxxxxxxx/stream"
MY_API_KEY = "sk-usr-xxxxxxxxxxxxxxxxxxxxxxx"
CHANNEL_ID = "xxxxxxxxxxxxxxxxxxxxxxxxx"

# ====================== CONFIGURAÇÃO DO USER_INFO ======================
# Aqui pode definir as informações do utilizador que quer passar para o agente

DEFAULT_USER_INFO = {
    "user_id": "user_12345",           # opcional - identificador único
    "name": "Utilizador XPTO",      # opcional
    "email": "",                       # opcional
    "segment": "cliente",              # exemplo: cliente, lead, suporte, etc.
    "language": "pt",                  # idioma
    "custom_field_1": "",              # pode adicionar quantos campos quiseres
    # Adiciona aqui qualquer informação que o seu agente use (ex: plano, tentativas, etc.)
}

# ======================================================================

@app.post("/v1/chat/completions")
async def proxy_openai_to_iaedu(request: Request):
    try:
        openai_data = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    # Extração da mensagem do utilizador
    messages = openai_data.get("messages", [])
    user_message = ""
    if messages:
        last_content = messages[-1].get("content", "")
        if isinstance(last_content, list):
            user_message = next((item.get("text", "") for item in last_content if item.get("type") == "text"), "")
        else:
            user_message = str(last_content)

    # === USER_INFO DINÂMICO (melhor prática) ===
    # Podes sobrescrever o user_info vindo do OpenAI (muito útil no Flowise)
    user_info = openai_data.get("user_info") or openai_data.get("metadata", {}).get("user_info")
    
    if isinstance(user_info, str):
        try:
            user_info = json.loads(user_info)
        except:
            user_info = DEFAULT_USER_INFO
    elif not isinstance(user_info, dict):
        user_info = DEFAULT_USER_INFO

    # Garantir que é sempre um dict
    if not isinstance(user_info, dict):
        user_info = DEFAULT_USER_INFO

    # Payload para a iaedu.pt
    iaedu_payload = {
        "channel_id": CHANNEL_ID,
        "thread_id": openai_data.get("user") or str(uuid.uuid4()),
        "user_info": json.dumps(user_info),        # ← Tem de ser string JSON (não dict!)
        "message": user_message
    }

headers = {"x-api-key": MY_API_KEY}
    is_stream = openai_data.get("stream", False)
    run_id = f"chatcmpl-{uuid.uuid4()}"
    created = int(time.time())

    try:
        if is_stream:
            return await handle_stream(iaedu_payload, headers, run_id, created)
        else:
            return await handle_non_stream(iaedu_payload, headers, run_id, created)
    except httpx.RequestError as exc:
        raise HTTPException(status_code=502, detail=f"Error contacting IAedu: {exc}")


async def handle_stream(iaedu_payload, headers, run_id, created):
    """Streaming response compatible with OpenAI + Flowise"""
    async def generate():
        async with client.stream("POST", TARGET_ENDPOINT, headers=headers, json=iaedu_payload) as resp:
            resp.raise_for_status()
            buffer = ""
            async for chunk in resp.aiter_bytes():
                if not chunk:
                    continue
                buffer += chunk.decode("utf-8", errors="ignore")

                # Split on possible concatenated JSON objects
                while "}{" in buffer:
                    idx = buffer.find("}{") + 1
                    part, buffer = buffer[:idx], buffer[idx:]
                    yield process_chunk(part, run_id, created)

                # Process remaining
                if buffer.strip():
                    yield process_chunk(buffer, run_id, created)
                    buffer = ""

        # Final stop chunk (very important for Flowise / some clients)
        stop_chunk = {
            "id": run_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": "gpt-4o-mini",
            "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}]
        }
        yield f"data: {json.dumps(stop_chunk)}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def process_chunk(raw_part: str, run_id: str, created: int):
    try:
        data = json.loads(raw_part.strip())
        if data.get("type") == "token":
            content = data.get("content", "")
            if content:
                chunk_data = {
                    "id": run_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": "gpt-4o-mini",
                    "choices": [{
                        "index": 0,
                        "delta": {"content": content},   # removed redundant "role"
                        "finish_reason": None
                    }]
                }
                return f"data: {json.dumps(chunk_data)}\n\n"
    except Exception:
        pass  # ignore malformed chunks
    return ""


async def handle_non_stream(iaedu_payload, headers, run_id, created):
    """Non-streaming response with strong resilience for Flowise Condition Agent"""
    full_text = ""

    async with client.stream("POST", TARGET_ENDPOINT, headers=headers, json=iaedu_payload) as resp:
        resp.raise_for_status()
        async for chunk in resp.aiter_bytes():
            if chunk:
                raw = chunk.decode("utf-8", errors="ignore")
                parts = raw.replace("}{", "}\n{").split("\n")
                for part in parts:
                    part = part.strip()
                    if not part:
                        continue
                    try:
                        data = json.loads(part)
                        if data.get("type") == "token":
                            full_text += data.get("content", "")
                    except Exception:
                        continue

    cleaned = full_text.strip()

    # === Resilience for Flowise ===
    has_json = False
    if "{" in cleaned and "}" in cleaned:
        try:
            start = cleaned.find("{")
            end = cleaned.rfind("}") + 1
            maybe_json = cleaned[start:end]
            json.loads(maybe_json)  # validate
            cleaned = maybe_json
            has_json = True
        except Exception:
            pass

    # If it's plain text (not JSON) → Force a safe JSON for Condition Agent nodes
    if not has_json and cleaned:
        print(f"DEBUG | IAedu returned plain text. Forcing JSON fallback for Flowise.")
        # You can customize this fallback message
        fallback = (
            "Do not choose this scenario if tentativa value is segunda. "
            "User is greeting you, saying good morning, good afternoon, etc., thanks you. "
            "Also if the user does not have a question, not asking you something or doesn't give you an order or specific request. "
            "Do not use to reply with specific information (it has no knowledge)."
        )
        cleaned = json.dumps({"output": fallback})

    if not cleaned:
        cleaned = json.dumps({"output": "Default Scenario: Use when others don't fit..."})

    response_body = {
        "id": run_id,
        "object": "chat.completion",
        "created": created,
        "model": "gpt-4o-mini",
        "choices": [{
            "index": 0,
            "message": {"role": "assistant", "content": cleaned},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 10, "completion_tokens": len(cleaned)//4 or 10, "total_tokens": 20}
    }

    print(f"DEBUG | Sent to Flowise: {cleaned[:300]}{'...' if len(cleaned)>300 else ''}")
    return JSONResponse(content=response_body)


@app.get("/v1")
async def health_check():
    return {"status": "proxy_online", "model": "gpt-4o-mini-iaedu-proxy", "port": 8008}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)    

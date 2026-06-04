"""
Chat Handler API — Unified API Proxy with Agent Tool Calling (supporting Gemini and ChatGPT/OpenAI).

Integrates Gemini or OpenAI/ChatGPT dynamically to call Level 1, 2, and 3 review tools
and stream the execution status and final answer back to the frontend.
"""

import json
import os
import urllib.request
import urllib.error
import datetime
import tools

# Try importing google.generativeai for Gemini support
try:
    import google.generativeai as genai
    from google.ai.generativelanguage import FunctionDeclaration, Tool, Schema, Type
except ImportError:
    pass

from chat_handler import SYSTEM_PROMPT, TOOLS_SPEC, TOOL_MAPPING, is_conversational_query

# Load .env file
def load_dotenv():
    paths = [".env", os.path.join(os.path.dirname(__file__), "..", ".env")]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, val = line.split("=", 1)
                            os.environ[key.strip()] = val.strip().strip('"').strip("'")
                break
            except Exception:
                pass

load_dotenv()

# ──────────────────────────────────────────────────────────────────────
# GEMINI TOOL BUILDERS
# ──────────────────────────────────────────────────────────────────────

try:
    TYPE_MAP = {
        "string": Type.STRING,
        "integer": Type.INTEGER,
        "number": Type.NUMBER,
        "object": Type.OBJECT,
        "array": Type.ARRAY,
        "boolean": Type.BOOLEAN
    }
except NameError:
    TYPE_MAP = {}

def dict_to_schema(d):
    if not isinstance(d, dict):
        return None
        
    s_type_str = d.get("type")
    s_type = TYPE_MAP.get(s_type_str, Type.TYPE_UNSPECIFIED)
    
    properties = {}
    if "properties" in d:
        for k, v in d["properties"].items():
            properties[k] = dict_to_schema(v)
            
    items = None
    if "items" in d:
        items = dict_to_schema(d["items"])
        
    required = d.get("required")
    description = d.get("description")
    enum = d.get("enum")
    
    return Schema(
        type=s_type,
        properties=properties or None,
        required=required or None,
        items=items,
        description=description,
        enum=enum
    )

def make_gemini_tools(tools_spec):
    decls = []
    for spec in tools_spec:
        if spec.get("type") == "function":
            func_info = spec["function"]
            name = func_info["name"]
            description = func_info["description"]
            params_dict = func_info.get("parameters")
            
            params_schema = dict_to_schema(params_dict) if params_dict else None
            
            decl = FunctionDeclaration(
                name=name,
                description=description,
                parameters=params_schema
            )
            decls.append(decl)
    return [Tool(function_declarations=decls)]


# ──────────────────────────────────────────────────────────────────────
# OPENAI / CHATGPT API CALLERS
# ──────────────────────────────────────────────────────────────────────

def call_openai_api(api_key, model, messages, tools=None, stream=False):
    payload = {
        "model": model,
        "messages": messages,
        "stream": stream
    }
    if tools:
        payload["tools"] = tools

    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        method="POST"
    )

    if stream:
        return urllib.request.urlopen(req, timeout=120)

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        print(f"[OpenAICall] Error: {e}")
        raise e


# ──────────────────────────────────────────────────────────────────────
# RESPONSE HELPERS
# ──────────────────────────────────────────────────────────────────────

def _send_sse(handler, data):
    """Send a single SSE event."""
    sse_data = json.dumps(data, ensure_ascii=False)
    handler.wfile.write(f"data: {sse_data}\n\n".encode("utf-8"))
    handler.wfile.flush()


def _send_json(handler, data, status=200):
    """Send a JSON response."""
    response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(response_bytes)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(response_bytes)


def _try_send_sse_error(handler, error_msg):
    """Try to send an error as SSE event."""
    try:
        _send_sse(handler, {"error": error_msg, "done": True})
    except Exception:
        pass


# ──────────────────────────────────────────────────────────────────────
# MAIN CHAT ROUTER
# ──────────────────────────────────────────────────────────────────────

def handle_chat_request(handler):
    """
    Handle POST /api/chat — executes tool calling loops and streams answers back as SSE.
    """
    # ── Parse request body ──
    try:
        content_length = int(handler.headers.get("Content-Length", 0))
        body = handler.rfile.read(content_length)
        payload = json.loads(body.decode("utf-8"))
    except Exception as e:
        _send_json(handler, {"error": f"Invalid request body: {e}"}, status=400)
        return

    user_message = payload.get("message", "").strip()
    history = payload.get("history", [])

    if not user_message:
        _send_json(handler, {"error": "Message is required"}, status=400)
        return

    # ── Start SSE response to browser ──
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "keep-alive")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()

    # Make sure env is fresh
    load_dotenv()
    provider = os.environ.get("MODEL_PROVIDER", "gemini").lower()

    if provider == "gemini":
        _handle_gemini_flow(handler, user_message, history)
    elif provider in ["openai", "chatgpt"]:
        _handle_openai_flow(handler, user_message, history)
    else:
        _try_send_sse_error(handler, f"Model provider '{provider}' không hỗ trợ hoặc chưa cấu hình đúng.")


# ──────────────────────────────────────────────────────────────────────
# PROVIDER FLOWS
# ──────────────────────────────────────────────────────────────────────

def _handle_gemini_flow(handler, user_message, history):
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    gemini_model_name = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    if not gemini_api_key or gemini_api_key.startswith("YOUR_GEMINI_"):
        _try_send_sse_error(handler, "Vui lòng cấu hình GEMINI_API_KEY hợp lệ trong file .env trước khi bắt đầu.")
        return

    # Ensure google.generativeai is configured
    try:
        import google.generativeai as genai
        from google.ai.generativelanguage import FunctionDeclaration, Tool, Schema, Type
        genai.configure(api_key=gemini_api_key, transport="rest")
    except Exception as e:
        _try_send_sse_error(handler, f"Lỗi khởi tạo Gemini SDK: {str(e)}")
        return

    current_date = datetime.date.today().strftime("%Y-%m-%d")
    dynamic_prompt = SYSTEM_PROMPT.format(current_date=current_date)

    # Convert conversation history to Gemini format
    gemini_history = []
    for msg in history[-20:]:
        role = "user" if msg.get("role") == "user" else "model"
        content = msg.get("content", "")
        gemini_history.append({
            "role": role,
            "parts": [content]
        })

    # Optimize simple greetings
    if is_conversational_query(user_message):
        try:
            model = genai.GenerativeModel(model_name=gemini_model_name, system_instruction=dynamic_prompt)
            chat = model.start_chat(history=gemini_history)
            response_stream = chat.send_message(user_message, stream=True)
            for chunk in response_stream:
                if chunk.text:
                    _send_sse(handler, {"token": chunk.text, "done": False})
            _send_sse(handler, {"token": "", "done": True})
            return
        except Exception as e:
            _try_send_sse_error(handler, f"Lỗi gọi Gemini API: {str(e)}")
            return

    # Full Agent Tool calling
    try:
        gemini_tools = make_gemini_tools(TOOLS_SPEC)
        model = genai.GenerativeModel(
            model_name=gemini_model_name,
            system_instruction=dynamic_prompt,
            tools=gemini_tools
        )
        chat = model.start_chat(history=gemini_history)
        current_input = user_message

        for loop_idx in range(5):
            if isinstance(current_input, str):
                response_stream = chat.send_message(current_input, stream=True)
            else:
                response_stream = chat.send_message([current_input], stream=True)
            function_to_call = None
            
            for chunk in response_stream:
                if chunk.candidates and chunk.candidates[0].content.parts:
                    for part in chunk.candidates[0].content.parts:
                        if part.text:
                            _send_sse(handler, {"token": part.text, "done": False})
                        elif part.function_call:
                            function_to_call = part.function_call
                            break
                if function_to_call:
                    break
            
            if function_to_call:
                response_stream.resolve()
                name = function_to_call.name
                args = dict(function_to_call.args)
                
                if "limit" in args:
                    try:
                        args["limit"] = int(args["limit"])
                    except Exception:
                        pass
                
                args_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in args.items())
                status_token = f"\n\n> 🔍 *InsightAgent đang chạy công cụ:* `{name}({args_str})`...\n\n"
                _send_sse(handler, {"token": status_token, "done": False})
                
                func = TOOL_MAPPING.get(name)
                if func:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = {"error": f"Lỗi thực thi công cụ: {str(e)}"}
                else:
                    result = {"error": f"Công cụ '{name}' không tồn tại."}
                
                current_input = genai.protos.Part(
                    function_response=genai.protos.FunctionResponse(
                        name=name,
                        response={"result": result}
                    )
                )
            else:
                break
                
        _send_sse(handler, {"token": "", "done": True})
    except Exception as e:
        _try_send_sse_error(handler, f"Lỗi thực thi vòng lặp Agent (Gemini): {str(e)}")


def _handle_openai_flow(handler, user_message, history):
    openai_api_key = os.environ.get("OPENAI_API_KEY")
    openai_model_name = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

    if not openai_api_key or openai_api_key.startswith("YOUR_OPENAI_"):
        _try_send_sse_error(handler, "Vui lòng cấu hình OPENAI_API_KEY hợp lệ trong file .env trước khi bắt đầu.")
        return

    current_date = datetime.date.today().strftime("%Y-%m-%d")
    dynamic_prompt = SYSTEM_PROMPT.format(current_date=current_date)

    # Convert conversation history to OpenAI format
    current_messages = [{"role": "system", "content": dynamic_prompt}]
    for msg in history[-20:]:
        current_messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    current_messages.append({"role": "user", "content": user_message})

    # Optimize simple conversational queries
    if is_conversational_query(user_message):
        try:
            response_stream = call_openai_api(openai_api_key, openai_model_name, current_messages, stream=True)
            for line in response_stream:
                line_str = line.decode("utf-8").strip()
                if not line_str or line_str == "data: [DONE]":
                    continue
                if line_str.startswith("data: "):
                    try:
                        chunk = json.loads(line_str[6:])
                        token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        if token:
                            _send_sse(handler, {"token": token, "done": False})
                    except Exception:
                        pass
            _send_sse(handler, {"token": "", "done": True})
            return
        except Exception as e:
            _try_send_sse_error(handler, f"Lỗi gọi OpenAI API: {str(e)}")
            return

    # Full Agent Tool calling
    try:
        for loop_idx in range(5):
            # Check for tool calls (non-streaming)
            response = call_openai_api(openai_api_key, openai_model_name, current_messages, tools=TOOLS_SPEC, stream=False)
            choice = response.get("choices", [{}])[0]
            message = choice.get("message", {})
            tool_calls = message.get("tool_calls", [])

            if not tool_calls:
                # Final response reached, stream it to browser
                response_stream = call_openai_api(openai_api_key, openai_model_name, current_messages, tools=TOOLS_SPEC, stream=True)
                for line in response_stream:
                    line_str = line.decode("utf-8").strip()
                    if not line_str or line_str == "data: [DONE]":
                        continue
                    if line_str.startswith("data: "):
                        try:
                            chunk = json.loads(line_str[6:])
                            token = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                            if token:
                                _send_sse(handler, {"token": token, "done": False})
                        except Exception:
                            pass
                break

            # Append model turn to history
            current_messages.append(message)

            # Execute tool calls
            for tc in tool_calls:
                tc_id = tc.get("id")
                func_info = tc.get("function", {})
                name = func_info.get("name")
                args_str = func_info.get("arguments", "{}")
                try:
                    args = json.loads(args_str)
                except Exception:
                    args = {}

                if "limit" in args:
                    try:
                        args["limit"] = int(args["limit"])
                    except Exception:
                        pass

                args_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in args.items())
                status_token = f"\n\n> 🔍 *InsightAgent đang chạy công cụ:* `{name}({args_str})`...\n\n"
                _send_sse(handler, {"token": status_token, "done": False})

                func = TOOL_MAPPING.get(name)
                if func:
                    try:
                        result = func(**args)
                    except Exception as e:
                        result = {"error": f"Lỗi thực thi công cụ: {str(e)}"}
                else:
                    result = {"error": f"Công cụ '{name}' không tồn tại."}

                current_messages.append({
                    "role": "tool",
                    "tool_call_id": tc_id,
                    "name": name,
                    "content": json.dumps(result, ensure_ascii=False)
                })

        _send_sse(handler, {"token": "", "done": True})
    except Exception as e:
        _try_send_sse_error(handler, f"Lỗi thực thi vòng lặp Agent (OpenAI): {str(e)}")

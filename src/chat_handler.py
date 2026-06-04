"""
Chat Handler — Ollama Proxy with Agent Tool Calling (Function Calling).

Integrates Qwen 2.5 via Ollama to call Level 1, 2, and 3 review tools dynamically
and stream the execution status and final answer back to the frontend.
"""

import json
import os
import urllib.request
import urllib.error
import tools

# LLM Provider Configuration
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "ollama").lower()

# Ollama Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")
OLLAMA_TEMPERATURE = float(os.environ.get("OLLAMA_TEMPERATURE", "0.0"))
OLLAMA_NUM_CTX = int(os.environ.get("OLLAMA_NUM_CTX", "8192"))

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_API_URL = os.environ.get("OPENAI_API_URL", "https://api.openai.com/v1")

# Tool name to function mapping
TOOL_MAPPING = {
    "get_reviews": tools.get_reviews,
    "count_reviews": tools.count_reviews,
    "search_reviews": tools.search_reviews,
    "get_supporting_quotes": tools.get_supporting_quotes,
    "get_top_complaints": tools.get_top_complaints,
    "get_top_strengths": tools.get_top_strengths,
    "detect_emerging_issues": tools.detect_emerging_issues,
    "get_category_breakdown": tools.get_category_breakdown,
    "rank_branches": tools.rank_branches,
    "prioritize_risks": tools.prioritize_risks,
    "generate_weekly_summary": tools.generate_weekly_summary,
}

# Tools specifications list in Ollama format
TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "count_reviews",
            "description": "Đếm số đánh giá theo bộ lọc. Hãy luôn ưu tiên dùng công cụ này khi hỏi số lượng/thống kê thay vì dùng get_reviews.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "start_date": {"type": "string", "description": "Ngày bắt đầu (ISO)."},
                    "end_date": {"type": "string", "description": "Ngày kết thúc (ISO)."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng lọc."},
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral", "all"], "description": "Cảm xúc."},
                    "category": {"type": "string", "enum": ["FOOD", "SERVICE", "AMBIENCE", "PRICE", "OTHER", "all"], "description": "Danh mục."},
                    "subcategory": {"type": "string", "description": "Mã danh mục con."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_reviews",
            "description": "Lấy danh sách đánh giá chi tiết theo bộ lọc. Không dùng để đếm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "start_date": {"type": "string", "description": "Ngày bắt đầu."},
                    "end_date": {"type": "string", "description": "Ngày kết thúc."},
                    "sentiment": {"type": "string", "enum": ["positive", "negative", "neutral", "all"], "description": "Cảm xúc."},
                    "category": {"type": "string", "enum": ["FOOD", "SERVICE", "AMBIENCE", "PRICE", "OTHER", "all"], "description": "Danh mục."},
                    "subcategory": {"type": "string", "description": "Mã danh mục con."},
                    "limit": {"type": "integer", "description": "Số lượng tối đa."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_reviews",
            "description": "Tìm kiếm đánh giá theo từ khóa.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {"type": "string", "description": "Từ khóa tìm kiếm."},
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "start_date": {"type": "string", "description": "Ngày bắt đầu."},
                    "end_date": {"type": "string", "description": "Ngày kết thúc."},
                    "limit": {"type": "integer", "description": "Số lượng tối đa."}
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supporting_quotes",
            "description": "Lấy trích dẫn đánh giá làm bằng chứng cho một vấn đề.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "Mã vấn đề/danh mục con."},
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "limit": {"type": "integer", "description": "Số lượng tối đa."}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_complaints",
            "description": "Lấy các phàn nàn lớn nhất xếp theo Impact Score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."},
                    "limit": {"type": "integer", "description": "Giới hạn số lượng."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_strengths",
            "description": "Lấy các điểm mạnh lớn nhất dựa trên đánh giá tích cực.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."},
                    "limit": {"type": "integer", "description": "Giới hạn số lượng."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_emerging_issues",
            "description": "Phát hiện các vấn đề tiêu cực mới nổi lên tăng đột biến.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."},
                    "limit": {"type": "integer", "description": "Giới hạn số lượng."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_breakdown",
            "description": "Lấy tỷ lệ phân bổ đánh giá theo các danh mục lớn.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rank_branches",
            "description": "So sánh, xếp hạng chi nhánh theo tiêu chí.",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "enum": ["risk", "rating", "sentiment", "complaint_volume", "strength"], "description": "Tiêu chí xếp hạng."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."},
                    "limit": {"type": "integer", "description": "Số lượng chi nhánh tối đa."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prioritize_risks",
            "description": "Đề xuất ưu tiên xử lý rủi ro dựa trên Impact Score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {"type": "string", "description": "Tên chi nhánh."},
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."},
                    "limit": {"type": "integer", "description": "Giới hạn số lượng."}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_summary",
            "description": "Tạo báo cáo tổng hợp tuần bao gồm rủi ro, điểm mạnh và đề xuất hành động.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {"type": "string", "enum": ["7d", "30d"], "description": "Thời khoảng."}
                }
            }
        }
    }
]

SYSTEM_PROMPT = """Bạn là InsightAgent AI — trợ lý phân tích đánh giá khách hàng cho chuỗi nhà hàng.
Hôm nay là ngày: {current_date}.
Dữ liệu đánh giá thực tế hiện có trong hệ thống chỉ nằm trong khoảng từ 2026-05-05 đến 2026-05-09.

Bạn có quyền truy cập vào các công cụ phân tích và truy xuất dữ liệu đánh giá thực tế.
Hãy luôn gọi các công cụ phù hợp để lấy số liệu thực tế trước khi trả lời. Không đoán mò hay tự bịa số liệu.

Nguyên tắc gọi công cụ & chọn tham số:
1. Phân loại cảm xúc (sentiment):
   - 'khiếu nại', 'phàn nàn', 'đánh giá xấu', 'đánh giá tệ', 'chê', 'vấn đề', 'lỗi'... -> bắt buộc truyền sentiment='negative'.
   - 'khen', 'tốt', 'tích cực', 'hài lòng', 'ưu điểm', 'điểm mạnh'... -> bắt buộc truyền sentiment='positive'.
   - Chỉ truyền sentiment='all' khi người dùng hỏi chung chung về phản hồi/đánh giá mà không phân biệt tốt xấu.
2. Tham số thời gian (start_date, end_date, period):
   - KHÔNG tự tiện điền start_date/end_date theo ngày tương lai hoặc đoán mò một khoảng thời gian nằm ngoài dải dữ liệu 2026-05-05 đến 2026-05-09.
   - Nếu người dùng không hỏi một khoảng thời gian cụ thể (ví dụ không nói rõ 'từ ngày A đến ngày B'), hãy luôn ưu tiên truyền tham số `period` (ví dụ: '30d') hoặc KHÔNG truyền start_date/end_date để hệ thống tự động sử dụng khoảng thời gian dữ liệu thực tế.
3. Tên chi nhánh (branch_id):
   - Phải viết hoa đúng chuẩn chính tả các chữ cái đầu khi truyền vào công cụ (ví dụ: viết 'Lý Quốc Sư' thay vì 'lý quốc sư', 'Nguyễn Huệ' thay vì 'nguyễn huệ', 'Times City' thay vì 'times city', 'Giải Phóng' thay vì 'giải phóng').


Nguyên tắc trả lời:
1. Trả lời bằng tiếng Việt trừ khi người dùng hỏi bằng tiếng Anh.
2. Tiết kiệm token & Tập trung vào số liệu: Tuyệt đối KHÔNG viết các đoạn tóm tắt, giải thích dài dòng, phân tích rườm rà hay đưa ra lời khuyên chung chung. Hãy đi thẳng vào câu trả lời, trình bày trực tiếp các con số, số liệu thống kê thu được từ các công cụ dưới dạng bảng (markdown table), danh sách ngắn gọn hoặc trích dẫn thô để người dùng tự đánh giá.
3. Hiệu năng & Tối ưu: Nếu câu hỏi yêu cầu so sánh nhiều mặt hoặc nhiều chi nhánh, hoặc cần cả rủi ro lẫn điểm mạnh, hãy gọi tất cả các công cụ cần thiết SONG SONG trong cùng một lượt gọi để giảm số lượt xử lý (ví dụ: gọi đồng thời rank_branches và get_top_complaints).
4. Tiết kiệm ngữ cảnh (Context Window): Luôn truyền tham số `limit` nhỏ khi gọi các công cụ truy xuất dữ liệu (ví dụ: gán `limit=5` hoặc tối đa `limit=10` thay vì `20` hay `30`). Điều này giúp bảo vệ cửa sổ ngữ cảnh của hệ thống không bị quá tải và giúp model phản hồi nhanh hơn rất nhiều.

Nguyên tắc nghiêm ngặt (Guardrails):
1. KHÔNG ĐƯỢC trả lời bằng các câu nói hứa hẹn suông hoặc mô tả dự định hành động (ví dụ: "Tôi sẽ kiểm tra...", "Tôi sẽ gọi công cụ..."). Hãy gọi công cụ trước, sau đó trả lời TRỰC TIẾP và TRÌNH BÀY ĐẦY ĐỦ số liệu/kết quả lấy được từ công cụ.
2. Khi đã có kết quả từ các công cụ (như get_top_complaints, rank_branches,...), bắt buộc phải hiển thị nội dung chi tiết hoặc số liệu cụ thể của kết quả đó cho người dùng. TUYỆT ĐỐI không được báo cáo trống, không được dừng lại ở lời hứa hay giải thích lý do không hiển thị.
3. Tránh bình luận dài dòng về khoảng thời gian của dữ liệu trừ khi được hỏi. Tập trung cung cấp số liệu thực tế được trả về bởi công cụ.
"""


def call_llm(messages, tools=None, stream=False, provider=None):
    """Make an HTTP POST request to the configured LLM provider (Ollama or OpenAI)."""
    selected_provider = provider if provider else LLM_PROVIDER
    if selected_provider == "openai":
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY chưa được cấu hình. Vui lòng thiết lập biến môi trường này khi chạy server.")
        payload = {
            "model": OPENAI_MODEL,
            "messages": messages,
            "stream": stream,
            "temperature": OLLAMA_TEMPERATURE
        }
        if tools:
            payload["tools"] = tools
            
        req = urllib.request.Request(
            f"{OPENAI_API_URL}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            },
            method="POST"
        )
    else:  # Default: ollama
        payload = {
            "model": OLLAMA_MODEL,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": OLLAMA_TEMPERATURE,
                "num_ctx": OLLAMA_NUM_CTX
            }
        }
        if tools:
            payload["tools"] = tools

        req = urllib.request.Request(
            f"{OLLAMA_URL}/api/chat",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
    if stream:
        return urllib.request.urlopen(req, timeout=120)
        
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            raw_res = json.loads(body.decode("utf-8"))
            
            # Map OpenAI response format to Ollama message output format
            if selected_provider == "openai":
                choices = raw_res.get("choices", [])
                if not choices:
                    return {}
                choice = choices[0]
                openai_msg = choice.get("message", {})
                
                mapped_msg = {
                    "role": "assistant",
                    "content": openai_msg.get("content") or ""
                }
                
                # Check for tool calls
                openai_tool_calls = openai_msg.get("tool_calls", [])
                if openai_tool_calls:
                    mapped_tool_calls = []
                    for tc in openai_tool_calls:
                        func_info = tc.get("function", {})
                        args_raw = func_info.get("arguments", "{}")
                        try:
                            args_parsed = json.loads(args_raw)
                        except Exception:
                            args_parsed = {}
                        mapped_tool_calls.append({
                            "id": tc.get("id"),
                            "type": "function",
                            "function": {
                                "name": func_info.get("name"),
                                "arguments": args_parsed
                            }
                        })
                    mapped_msg["tool_calls"] = mapped_tool_calls
                
                return {"message": mapped_msg}
            else:
                return raw_res
    except Exception as e:
        print(f"[LLMCall] Error calling non-streaming {selected_provider}: {e}")
        return {}


def is_conversational_query(message):
    """Detect if the message is a simple conversational greeting or general statement."""
    msg_lower = message.lower().strip("?,.!")
    greetings = {
        "hi", "hello", "xin chào", "xin chao", "chào", "chao",
        "bạn là ai", "ban la ai", "ai đó", "ai do",
        "help", "trợ giúp", "tro giup", "hướng dẫn", "huong dan",
        "tên bạn là gì", "ten ban la gi"
    }
    if msg_lower in greetings:
        return True
    words = msg_lower.split()
    if len(words) <= 2 and any(w in msg_lower for w in ["cảm ơn", "cam on", "thanks", "thank", "ok", "oke"]):
        return True
    return False


def _stream_final_response(handler, messages, provider=None):
    """Stream final text tokens from LLM to the browser."""
    selected_provider = provider if provider else LLM_PROVIDER
    try:
        with call_llm(messages, stream=True, provider=selected_provider) as resp:
            for line_bytes in resp:
                line = line_bytes.decode("utf-8").strip()
                if not line:
                    continue
                
                if selected_provider == "openai":
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            _send_sse(handler, {"token": "", "done": True})
                            break
                        try:
                            chunk = json.loads(data_str)
                            choices = chunk.get("choices", [])
                            if choices:
                                token = choices[0].get("delta", {}).get("content", "")
                                if token:
                                    _send_sse(handler, {"token": token, "done": False})
                        except json.JSONDecodeError:
                            continue
                else:  # Default: ollama
                    try:
                        chunk = json.loads(line)
                        token = chunk.get("message", {}).get("content", "")
                        done = chunk.get("done", False)

                        if token:
                            _send_sse(handler, {"token": token, "done": False})

                        if done:
                            _send_sse(handler, {"token": "", "done": True})
                            break
                    except json.JSONDecodeError:
                        continue

    except urllib.error.URLError as e:
        error_msg = (
            f"Không thể kết nối đến {selected_provider.upper()}. "
            f"Hãy chắc chắn dịch vụ đang chạy. Lỗi: {e}"
        )
        _try_send_sse_error(handler, error_msg)

    except Exception as e:
        _try_send_sse_error(handler, f"Lỗi server: {str(e)}")


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
    provider = payload.get("provider", "").strip().lower()
    if provider not in ["ollama", "openai"]:
        provider = LLM_PROVIDER

    if not user_message:
        _send_json(handler, {"error": "Message is required"}, status=400)
        return

    # ── Start SSE response to browser ──
    handler.send_response(200)
    handler.send_header("Content-Type", "text/event-stream; charset=utf-8")
    handler.send_header("Cache-Control", "no-cache")
    handler.send_header("Connection", "close")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.close_connection = True

    # Build conversation messages history
    import datetime
    current_date = datetime.date.today().strftime("%Y-%m-%d")
    dynamic_prompt = SYSTEM_PROMPT.format(current_date=current_date)
    messages = [{"role": "system", "content": dynamic_prompt}]
    for msg in history[-10:]:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    messages.append({"role": "user", "content": user_message})

    # ── Optimize simple conversational queries ──
    if is_conversational_query(user_message):
        _stream_final_response(handler, messages, provider=provider)
        return

    # ── Tool calling loop (max 5 iterations) ──
    has_called_tools = False
    
    for loop_idx in range(5):
        # Call LLM non-streaming to inspect if it wants to run tool calls
        response = call_llm(messages, tools=TOOLS_SPEC, stream=False, provider=provider)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            final_text = message.get("content", "")
            if final_text:
                _stream_text_response(handler, final_text)
                return
            break

        has_called_tools = True
        
        # Save assistant message with tool calls in history
        messages.append(message)

        # Execute each tool call
        for tc in tool_calls:
            func_info = tc.get("function", {})
            name = func_info.get("name")
            arguments = func_info.get("arguments", {})

            # Clean and sanitize arguments
            if "limit" in arguments:
                try:
                    arguments["limit"] = int(arguments["limit"])
                except Exception:
                    pass

            # Format trace representation for the chat stream
            args_str = ", ".join(f"{k}={repr(v)}" for k, v in arguments.items())
            status_token = f"\n\n> 🔍 *InsightAgent đang chạy công cụ:* `{name}({args_str})`...\n\n"
            _send_sse(handler, {"token": status_token, "done": False})

            # Execute tool locally
            func = TOOL_MAPPING.get(name)
            if func:
                try:
                    result = func(**arguments)
                except Exception as e:
                    result = {"error": f"Lỗi thực thi công cụ: {str(e)}"}
            else:
                result = {"error": f"Công cụ '{name}' không tồn tại."}

            # Append tool output to history
            tool_msg = {
                "role": "tool",
                "name": name,
                "content": json.dumps(result, ensure_ascii=False)
            }
            if tc.get("id"):
                tool_msg["tool_call_id"] = tc.get("id")
            messages.append(tool_msg)

    # ── Final Response Generation (Streaming) ──
    _stream_final_response(handler, messages, provider=provider)


def _stream_text_response(handler, text, chunk_size=8, delay_sec=0.001):
    """
    Stream a pre-generated string back to the browser via SSE,
    simulating active generation with high speed.
    """
    import time
    i = 0
    while i < len(text):
        chunk = text[i:i+chunk_size]
        _send_sse(handler, {"token": chunk, "done": False})
        i += chunk_size
        time.sleep(delay_sec)
    _send_sse(handler, {"token": "", "done": True})


# ──────────────────────────────────
# Helper functions
# ──────────────────────────────────

def _send_json(handler, data, status=200):
    """Send a JSON response."""
    response_bytes = json.dumps(data, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(response_bytes)))
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.end_headers()
    handler.wfile.write(response_bytes)


def _send_sse(handler, data):
    """Send a single SSE event."""
    sse_data = json.dumps(data, ensure_ascii=False)
    handler.wfile.write(f"data: {sse_data}\n\n".encode("utf-8"))
    handler.wfile.flush()


def _try_send_sse_error(handler, error_msg):
    """Try to send an error as SSE event."""
    try:
        _send_sse(handler, {"error": error_msg, "done": True})
    except Exception:
        pass

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

# Ollama Configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:9b")

# Tool name to function mapping
TOOL_MAPPING = {
    "get_reviews": tools.get_reviews,
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
            "name": "get_reviews",
            "description": "Lấy danh sách các đánh giá khách hàng (reviews) gốc đã được phân tích theo bộ lọc chi nhánh, khoảng thời gian, loại cảm xúc, hoặc danh mục.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên chi nhánh hoặc ID chi nhánh (ví dụ: 'Times City', 'Nguyễn Huệ')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Ngày bắt đầu lọc (định dạng ISO, ví dụ: '2026-05-01')."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Ngày kết thúc lọc (định dạng ISO, ví dụ: '2026-06-04')."
                    },
                    "sentiment": {
                        "type": "string",
                        "enum": ["positive", "negative", "neutral", "all"],
                        "description": "Cảm xúc cần lọc."
                    },
                    "category": {
                        "type": "string",
                        "enum": ["FOOD", "SERVICE", "AMBIENCE", "PRICE", "OTHER", "all"],
                        "description": "Danh mục chính cần lọc."
                    },
                    "subcategory": {
                        "type": "string",
                        "description": "Danh mục con cụ thể cần lọc (ví dụ: 'SERVICE_WAIT_TIME')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng đánh giá tối đa trả về (mặc định 50)."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_reviews",
            "description": "Tìm kiếm đánh giá khách hàng bằng từ khóa trong nội dung hoặc bằng chứng (evidence).",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm (ví dụ: 'nguội', 'đợi lâu', 'khuyến mãi')."
                    },
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh cần giới hạn tìm kiếm."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Ngày bắt đầu lọc."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Ngày kết thúc lọc."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng tối đa."
                    }
                },
                "required": ["keyword"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_supporting_quotes",
            "description": "Lấy danh sách các trích dẫn bằng chứng (quotes) cụ thể của khách hàng cho một vấn đề hoặc danh mục con.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {
                        "type": "string",
                        "description": "Mã vấn đề cần trích dẫn (ví dụ: 'SERVICE_WAIT_TIME', 'FOOD_TEMPERATURE')."
                    },
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng trích dẫn tối đa (mặc định 5)."
                    }
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_complaints",
            "description": "Lấy danh sách các khiếu nại (phàn nàn) lớn nhất của khách hàng sắp xếp theo Impact Score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian phân tích ('7d' hoặc '30d')."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng khiếu nại tối đa cần lấy."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_top_strengths",
            "description": "Lấy danh sách các điểm mạnh (lời khen) lớn nhất của thương hiệu dựa trên các đánh giá tích cực.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian phân tích."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng tối đa."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "detect_emerging_issues",
            "description": "Phát hiện các vấn đề bất thường mới nổi (emerging issues) có lượt phàn nàn tăng đột biến trong tuần qua.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian phân tích."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng tối đa."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_category_breakdown",
            "description": "Lấy phân bổ tỷ trọng của các khía cạnh đánh giá theo các danh mục lớn (FOOD, SERVICE, AMBIENCE, PRICE, OTHER).",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rank_branches",
            "description": "So sánh và xếp hạng các chi nhánh nhà hàng dựa trên các tiêu chí (risk, rating, sentiment, complaint_volume, strength).",
            "parameters": {
                "type": "object",
                "properties": {
                    "metric": {
                        "type": "string",
                        "enum": ["risk", "rating", "sentiment", "complaint_volume", "strength"],
                        "description": "Tiêu chí xếp hạng."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng chi nhánh tối đa trả về."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "prioritize_risks",
            "description": "Đề xuất và xếp hạng các rủi ro vận hành cần ưu tiên xử lý trước dựa trên Impact Score.",
            "parameters": {
                "type": "object",
                "properties": {
                    "branch_id": {
                        "type": "string",
                        "description": "Tên hoặc ID chi nhánh."
                    },
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian."
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Số lượng tối đa."
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "generate_weekly_summary",
            "description": "Tạo báo cáo tổng hợp tình hình đánh giá tuần này bao gồm top rủi ro, điểm mạnh, chi nhánh tốt/tệ nhất và khuyến nghị hành động.",
            "parameters": {
                "type": "object",
                "properties": {
                    "period": {
                        "type": "string",
                        "enum": ["7d", "30d"],
                        "description": "Khoảng thời gian của báo cáo."
                    }
                }
            }
        }
    }
]

SYSTEM_PROMPT = """Bạn là InsightAgent AI — trợ lý phân tích đánh giá khách hàng cho chuỗi nhà hàng.
Bạn có quyền truy cập vào các công cụ phân tích và truy xuất dữ liệu đánh giá thực tế.
Hãy luôn gọi các công cụ phù hợp để lấy số liệu thực tế trước khi trả lời. Không đoán mò hay tự bịa số liệu.

Nguyên tắc trả lời:
1. Trả lời bằng tiếng Việt trừ khi người dùng hỏi bằng tiếng Anh.
2. Trình bày số liệu rõ ràng, dễ hiểu (sử dụng danh sách dấu đầu dòng hoặc bảng biểu).
3. Luôn dẫn ra các trích dẫn đánh giá thực tế (quotes) làm bằng chứng khi thảo luận về khiếu nại hay khen ngợi cụ thể.
4. Đề xuất các hành động cải thiện cụ thể, thực tế và xếp theo mức độ nghiêm trọng hoặc Impact Score.
"""


def call_ollama(messages, tools=None, stream=False):
    """Make an HTTP POST request to Ollama chat endpoint."""
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": stream
    }
    if tools:
        payload["tools"] = tools

    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    # If streaming, return the open response stream
    if stream:
        return urllib.request.urlopen(req, timeout=120)
    
    # Non-streaming, return parsed JSON
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = resp.read()
            return json.loads(body.decode("utf-8"))
    except Exception as e:
        print(f"[OllamaCall] Error calling non-streaming Ollama: {e}")
        return {}


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

    # Build conversation messages history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in history[-20:]:
        messages.append({
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        })
    messages.append({"role": "user", "content": user_message})

    # ── Tool calling loop (max 5 iterations) ──
    has_called_tools = False
    
    for loop_idx in range(5):
        # Call Ollama non-streaming to inspect if it wants to run tool calls
        response = call_ollama(messages, tools=TOOLS_SPEC, stream=False)
        message = response.get("message", {})
        tool_calls = message.get("tool_calls", [])

        if not tool_calls:
            # No tool calls generated in this turn, we are ready to write final response
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
            messages.append({
                "role": "tool",
                "name": name,
                "content": json.dumps(result, ensure_ascii=False)
            })

    # ── Final Response Generation (Streaming) ──
    try:
        # Call Ollama one last time with stream=True to render final answer
        # Note: we omit tools here so it concentrates on formulating the text response
        with call_ollama(messages, stream=True) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line.decode("utf-8"))
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
            f"Không thể kết nối đến Ollama ({OLLAMA_URL}). "
            f"Hãy chắc chắn Ollama đang chạy. Lỗi: {e}"
        )
        _try_send_sse_error(handler, error_msg)

    except Exception as e:
        _try_send_sse_error(handler, f"Lỗi server: {str(e)}")


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

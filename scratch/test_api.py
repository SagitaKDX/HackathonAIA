import os
import sys
import json
import io

# Add src/ to import path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

class MockWFile:
    def __init__(self):
        self.output = []

    def write(self, data):
        text = data.decode("utf-8")
        # Print SSE tokens as they arrive
        if text.startswith("data: "):
            try:
                payload = json.loads(text[6:].strip())
                if "token" in payload:
                    token = payload["token"]
                    print(token, end="", flush=True)
                elif "error" in payload:
                    print(f"\n[Error] {payload['error']}")
            except Exception:
                pass
        self.output.append(data)

    def flush(self):
        pass

class MockHandler:
    def __init__(self, message, history=None):
        if history is None:
            history = []
        payload = {"message": message, "history": history}
        body = json.dumps(payload).encode("utf-8")
        
        self.headers = {"Content-Length": str(len(body))}
        self.rfile = io.BytesIO(body)
        self.wfile = MockWFile()
        self.headers_sent = []
        self.status_code = None

    def send_response(self, code):
        self.status_code = code

    def send_header(self, keyword, value):
        self.headers_sent.append((keyword, value))

    def end_headers(self):
        pass

def main():
    # Force UTF-8 encoding for Windows console display
    if sys.platform.startswith("win"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
            sys.stderr.reconfigure(encoding="utf-8")
        except Exception:
            pass

    from chat_handler_api import handle_chat_request, load_dotenv
    load_dotenv()

    provider = os.environ.get("MODEL_PROVIDER", "gemini").lower()
    print(f"=== TESTING API HANDLER ===")
    print(f"Provider: {provider.upper()}")
    if provider == "gemini":
        print(f"Model:    {os.environ.get('GEMINI_MODEL', 'gemini-2.5-flash')}")
    elif provider in ["openai", "chatgpt"]:
        print(f"Model:    {os.environ.get('OPENAI_MODEL', 'gpt-4o-mini')}")
    else:
        print(f"Provider '{provider}' not directly tested via API Handler.")
        return
    print("===========================\n")

    question = "Có bao nhiêu đánh giá xấu tại chi nhánh Nguyễn Huệ?"
    print(f"User: {question}")
    print("Bot: ", end="", flush=True)

    handler = MockHandler(message=question)
    handle_chat_request(handler)
    print("\n\n=== TEST COMPLETE ===")

if __name__ == "__main__":
    main()

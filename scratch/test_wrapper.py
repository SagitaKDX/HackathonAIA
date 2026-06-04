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
        self.output.append(data)

    def flush(self):
        pass

class MockHandler:
    def __init__(self, message, provider="ollama", history=None):
        if history is None:
            history = []
        payload = {
            "message": message,
            "history": history,
            "provider": provider
        }
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
    from server import handle_chat_request_wrapper
    
    print("Testing handle_chat_request_wrapper routing...")
    
    # 2. Test out-of-scope query check
    handler_out_of_scope = MockHandler("có thể viết cho tôi script python được hay không", provider="ollama")
    try:
        handle_chat_request_wrapper(handler_out_of_scope)
        # Check output buffer of MockWFile
        output_bytes = b"".join(handler_out_of_scope.wfile.output)
        output_str = output_bytes.decode("utf-8")
        print("Out-of-scope response:")
        print(output_str)
        if "phạm vi" in output_str:
            print("SUCCESS: Out-of-scope query successfully intercepted!")
        else:
            print("FAILED: Interception did not occur.")
    except Exception as e:
        print(f"Out-of-scope test got error: {e}")



if __name__ == "__main__":
    main()

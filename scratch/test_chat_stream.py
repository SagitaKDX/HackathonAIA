import urllib.request
import json

def test():
    req = urllib.request.Request(
        'http://localhost:8000/api/chat',
        data=json.dumps({'message': 'Có bao nhiêu đánh giá xấu?', 'history': []}).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    resp = urllib.request.urlopen(req)
    for line in resp:
        print(line.decode('utf-8').strip(), flush=True)

if __name__ == '__main__':
    test()

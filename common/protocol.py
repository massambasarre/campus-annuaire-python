import json

def send_json_line(sock, payload: dict):
    data = (json.dumps(payload) + "\n").encode("utf-8")
    sock.sendall(data)

def recv_json_line(sock, buffer: bytearray) -> dict | None:
    while True:
        nl = buffer.find(b"\n")
        if nl != -1:
            line = buffer[:nl]
            del buffer[:nl+1]
            if not line:
                return None
            return json.loads(line.decode("utf-8"))
        chunk = sock.recv(4096)
        if not chunk:
            return None
        buffer.extend(chunk)

def ok(data=None):
    from common.messages import STATUS_OK
    return {"status": STATUS_OK, "data": data}

def err(msg: str):
    from common.messages import STATUS_ERROR
    return {"status": STATUS_ERROR, "error": msg}

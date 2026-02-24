#!/usr/bin/env python3
"""
无前端对话：直接调用本地 Deep RAG 后端进行多轮对话。
需先启动后端: ./start-backend-only.sh  或  uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
import json
import sys
import os

# 确保能 import backend
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import httpx
except ImportError:
    print("请先安装依赖: pip install httpx")
    sys.exit(1)

API_BASE = os.environ.get("DEEP_RAG_API", "http://localhost:8000")


def chat(messages: list, provider: str = None) -> str:
    """发送消息并流式打印回复，返回最终助手回复文本。"""
    payload = {"messages": messages, "provider": provider}
    full_content = []
    with httpx.Client(timeout=120.0) as client:
        with client.stream("POST", f"{API_BASE}/chat", json=payload) as r:
            r.raise_for_status()
            buffer = ""
            for chunk in r.iter_text():
                if not chunk:
                    continue
                buffer += chunk
                while "\n" in buffer:
                    line, buffer = buffer.split("\n", 1)
                    line = line.strip()
                    if not line.startswith("data: "):
                        continue
                    try:
                        data = json.loads(line[6:])
                        if data.get("type") == "content" and data.get("content"):
                            print(data["content"], end="", flush=True)
                            full_content.append(data["content"])
                        elif data.get("type") == "tool_calls":
                            print("\n[检索文件中...]", flush=True)
                        elif data.get("type") == "done":
                            pass
                    except json.JSONDecodeError:
                        pass
    print()
    return "".join(full_content)


def main():
    print("Deep RAG 命令行对话 (后端: %s)" % API_BASE)
    print("输入内容回车发送，输入 q 或 exit 退出。\n")
    messages = []
    while True:
        try:
            user_input = input("你: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not user_input or user_input.lower() in ("q", "exit", "quit"):
            break
        messages.append({"role": "user", "content": user_input})
        print("助手: ", end="", flush=True)
        reply = chat(messages)
        messages.append({"role": "assistant", "content": reply})
        print()


if __name__ == "__main__":
    main()

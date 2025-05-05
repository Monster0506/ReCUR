import asyncio

from core.llm import EchoLLM


def test_echo_llm():
    llm = EchoLLM()
    text = asyncio.run(llm.generate("hello"))
    assert "hello" in text

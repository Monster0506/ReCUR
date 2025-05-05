import asyncio

from cli.recur_cli import pipeline


def test_pipeline_echo(tmp_path):
    cfg = {
        "prompt": "Say hi",
        "echo": True,
        "temperature": 0.4,
        "rounds": 1,
        "alts": 2,
    }
    final = asyncio.run(pipeline(cfg))
    assert final[0].text.startswith("[echo]")

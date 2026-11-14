import asyncio
import os

import uvicorn

from source.core.loop import selector_loop_factory


def main() -> None:
    config = uvicorn.Config(
        "source.server:app",
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", "8000")),
    )
    server = uvicorn.Server(config)
    with asyncio.Runner(loop_factory=selector_loop_factory) as runner:
        runner.run(server.serve())


if __name__ == "__main__":
    main()

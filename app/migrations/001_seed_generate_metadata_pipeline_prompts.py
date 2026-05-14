import asyncio
import sys
from pathlib import Path


APP_ROOT = Path(__file__).resolve().parents[1]
if str(APP_ROOT) not in sys.path:
    sys.path.insert(0, str(APP_ROOT))


from utils import pipeline_prompt_config


async def main() -> None:
    result = await pipeline_prompt_config.seed_default_pipeline_prompts()
    print(result)


if __name__ == "__main__":
    asyncio.run(main())
import time

from django.test import TestCase

# Create your tests here.

import asyncio

async def main():
    print('Hello ...123')
    await asyncio.sleep(10)
    print('... World!')

asyncio.run(main())
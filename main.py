from manager import Manager
import telegram
import asyncio

if __name__ == "__main__":
    x = Manager()
    x.start()
    asyncio.run(telegram.start())

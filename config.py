import os
from dotenv import load_dotenv


dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path)


class Config:
    TOKEN: str = str(os.environ.get('TOKEN'))

    DB_URL: str = str(os.environ.get('DB_URL'))


config = Config()

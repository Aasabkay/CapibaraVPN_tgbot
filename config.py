import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('BOT_TOKEN')
ADMIN_ID = int(os.getenv('ADMIN_ID'))
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
SERVER_IP = os.getenv('SERVER_IP')
ENCRYPTION = os.getenv('ENCRYPTION')
SERVICE_NAME = os.getenv('SERVICE_NAME')
PBK = os.getenv('PBK')
FP = os.getenv('FP')
SNI = os.getenv('SNI')
SID = os.getenv('SID')
SPX = os.getenv('SPX')
PQV = os.getenv('PQV')
PANEL_LOGIN = os.getenv('PANEL_LOGIN')
PANEL_PASSWORD = os.getenv('PANEL_PASSWORD')
PANEL_HOST = os.getenv('PANEL_HOST')
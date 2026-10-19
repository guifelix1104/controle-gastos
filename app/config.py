import os

from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY não definida. Crie o arquivo .env (veja o .env.example)."
    )

ALGORITMO = "HS256"
DIAS_DE_SESSAO = 7

# Em produção (HTTPS), use COOKIE_SECURE=true no .env
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
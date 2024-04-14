from app.core.config import settings
import uvicorn


def main():
    uvicorn.run("app.main:app", reload=True, host="0.0.0.0", port=settings.SERVER_PORT)


if __name__ == "__main__":
    main()

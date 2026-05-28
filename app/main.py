from bootstrap.app import fastapi_app
from bootstrap.logger import configure_logging

configure_logging()


app = fastapi_app()


def main():
    from lib.ext.uvicorn import UvicornOptions, run
    from settings import settings

    run(
        "main:app",
        UvicornOptions(
            host="0.0.0.0",
            port=settings.APP_PORT,
            log_level=settings.APP_LOG_LEVEL.lower(),
            reload=settings.APP_ENVIRONMENT.value == "development",
            workers=settings.APP_WORKERS_COUNT,
            timeout_keep_alive=65,
        ),
    )


if __name__ == "__main__":
    main()

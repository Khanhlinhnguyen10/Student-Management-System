
import os

from app import create_app


# Initialize Flask application
app = create_app()


if __name__ == "__main__":
    # Read development configuration
    debug_mode = (
        os.getenv("FLASK_DEBUG", "false").lower() == "true"
    )

    port = int(os.getenv("FLASK_PORT", "5000"))

    # Run local development server
    app.run(
        host="127.0.0.1",
        port=port,
        debug=debug_mode
    )

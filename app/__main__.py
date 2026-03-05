from __future__ import annotations

from .webapp import create_app


def main() -> None:
    app = create_app()
    # debug=True para facilitar durante o desafio
    app.run(host="127.0.0.1", port=5000, debug=True)


if __name__ == "__main__":
    main()

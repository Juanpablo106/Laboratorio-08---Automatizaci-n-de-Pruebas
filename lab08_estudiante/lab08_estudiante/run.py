"""Levanta la aplicación del laboratorio.

Uso:
    python run.py                 -> http://127.0.0.1:5000
    python run.py --port 5050
    python run.py --host 0.0.0.0  -> (dentro de Docker)
"""
import argparse

from app import crear_app

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    print(f"Inventario IS1 en http://{args.host}:{args.port}  (usuario: admin / Admin123)")
    crear_app().run(host=args.host, port=args.port, debug=False)

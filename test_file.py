import os
from pathlib import Path


class Usuario:
    activo = True
    edad: int = 20

    def saludar(self, nombre: str) -> str:
        return nombre


def ping(ip: str):
    pass
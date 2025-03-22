import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue

from fastapi import APIRouter, WebSocket


class SceneAbstract(ABC):
    def __init__(self):
        super().__init__()


import asyncio
from abc import ABC, abstractmethod
from asyncio import Queue

from fastapi import APIRouter, WebSocket


class ScreneAbstract(ABC):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def step(self, actions):
        pass

    @abstractmethod
    def reset(self):
        pass

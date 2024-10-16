"""The SolConnection class, used by the API Client."""

import asyncio
import json

import websockets.client

from .utils import BadRequest, MoreCapableEncoder


class SolConnection:
    """Underlying Connection Object to a Sol API endpoint. Do not use directly."""

    def __init__(self, sock: websockets.client.WebSocketClientProtocol):
        """Initializes with a socket object and request id counter."""
        self.sock = sock
        self._nextreqid = 0

    async def request(self, route, data, timeout=30):
        """Issues a request to Sol/SolMate.
        When the timeout passes, an asyncio.TimeoutError will be raised.
        """
        reqid = self.reqid_counter()
        await self.sock.send(json.dumps({"route": route, "id": reqid, "data": data}, cls=MoreCapableEncoder))
        response = json.loads(await asyncio.wait_for(self.sock.recv(), timeout))
        if "error" in response:
            raise BadRequest(response["error"])
        return response["data"]

    def reqid_counter(self):
        """Internal counter for request ids. In principle, this could be anything."""
        self._nextreqid += 1
        return self._nextreqid

    async def close(self, reason=""):
        """Close the socket."""
        await self.sock.close(code=1000, reason=reason)

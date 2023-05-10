# api endpoints
import gradio as gr
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from modules import script_callbacks as script_callbacks

def intersyncAPI(_: gr.Blocks, app: FastAPI):
	class ConnectionManager:
		def __init__(self):
			self.active_connections: list[WebSocket] = []
			self.last_message = None

		async def connect(self, websocket: WebSocket):
			await websocket.accept()
			self.active_connections.append(websocket)
			if not self.last_message == None:
				await websocket.send_text(last_message)

		def disconnect(self, websocket: WebSocket):
			self.active_connections.remove(websocket)

		async def broadcast_exempt(self, message: str, exempt: WebSocket):
			self.last_message = message
			for connection in self.active_connections:
				if exempt == connection:
					continue
				await connection.send_text(message)

	manager = ConnectionManager()

	@app.websocket('/intersync/connect')
	async def connect(websocket: WebSocket):
		await manager.connect(websocket)
		try:
			while True:
				text = await websocket.receive_text()
				await manager.broadcast_exempt(text, websocket)
		except WebSocketDisconnect:
			manager.disconnect(websocket)

script_callbacks.on_app_started(intersyncAPI)

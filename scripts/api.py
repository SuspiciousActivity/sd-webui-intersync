# api endpoints
import gradio as gr
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from modules import script_callbacks as script_callbacks
from modules import shared, progress

import base64
from io import BytesIO

def intersyncAPI(_: gr.Blocks, app: FastAPI):
	class ConnectionManager:
		def __init__(self):
			self.active_connections: list[WebSocket] = []
			self.last_message = None

		async def connect(self, websocket: WebSocket):
			await websocket.accept()
			self.active_connections.append(websocket)
			if not self.last_message == None:
				await websocket.send_text(self.last_message)

		def disconnect(self, websocket: WebSocket):
			self.active_connections.remove(websocket)

		async def broadcast_exempt(self, message: str, exempt: WebSocket):
			self.last_message = message
			for connection in self.active_connections:
				if exempt == connection:
					continue
				await connection.send_text(message)

	def imgToB64(img):
		buffered = BytesIO()
		img.save(buffered, format="JPEG")
		img_str = base64.b64encode(buffered.getvalue())
		img_base64 = bytes("data:image/jpeg;base64,", encoding='utf-8') + img_str
		return img_base64

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

	@app.get('/intersync/result/{task_id}')
	def result(task_id: str):
		for result in progress.recorded_results:
			if result[0] == task_id:
				data = result[1]
				return {
					'images': [imgToB64(img) for img in data[0]],
					'generation_info': data[1],
					'html_info': data[2],
					'html_log': data[3]
				}

script_callbacks.on_app_started(intersyncAPI)

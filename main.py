from fastapi import FastAPI, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from bs4 import BeautifulSoup
import openai
import email
import io

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción restringe el dominio
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalisisRequest(BaseModel):
    secciones: List[str]
    prompt: str
    api_key: str

@app.post("/procesar_eml")
async def procesar_eml(file: UploadFile):
    content = await file.read()
    msg = email.message_from_bytes(content)

    html = ""
    for part in msg.walk():
        if part.get_content_type() == "text/html":
            html = part.get_payload(decode=True).decode(part.get_content_charset(), errors="ignore")
            break

    soup = BeautifulSoup(html, "html.parser")
    bloques = soup.find_all("div")

    secciones = []
    for bloque in bloques:
        texto = bloque.get_text(separator=" ", strip=True)
        if any(clave in texto.upper() for clave in ["PROMOCIONES PLANES DE RENTA", "PROMOCIONES PREPAGO", "PORTFOLIO DE PRODUCTOS"]):
            titulo = texto[:120]
            secciones.append(titulo)

    return {"secciones": secciones}

@app.post("/analizar_secciones")
async def analizar_secciones(request: AnalisisRequest):
    openai.api_key = request.api_key

    resultados = []
    for descripcion in request.secciones:
        messages = [
            {"role": "system", "content": "Eres un asistente experto en análisis de promociones y portafolios de productos."},
            {"role": "user", "content": f"{request.prompt}

Texto:
{descripcion}"}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=messages,
            temperature=0.2,
        )
        resultado = response.choices[0].message.content.strip()
        resultados.append({"entrada": descripcion[:100], "respuesta": resultado})

    return {"resultados": resultados}

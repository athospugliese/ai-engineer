#!/usr/bin/env python
from fastapi import FastAPI
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from pydantic import BaseModel
from fastapi import Depends

from src.chain_get_foods import *

load_dotenv()

class InputQuery(BaseModel):
    path: str
    provider: str = "openai"
    
class OutputQuery(BaseModel):
    resultado: List[str]

def format_docs(docs):
    return "\n\n".join([d.page_content for d in docs])

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Setting up...")
    
    print("Setup done.")
    yield
    print("Cleaning up...")

app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple api server using Langchain's Runnable interfaces",
    lifespan=lifespan,
)

@app.get("/")
def read_root():
    return {"Status": "Running..."}

@app.get("/list-foods")
async def get_list_foods(input_query: InputQuery = Depends()):
    output = get_structured_foods(input_query.path, input_query.provider)
    return output

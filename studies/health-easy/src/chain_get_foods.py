import base64
import httpx
from langchain_core.messages import HumanMessage

from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from pydantic import BaseModel, Field
from typing import List
from langchain_groq import ChatGroq

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from dotenv import load_dotenv

load_dotenv()

model_name_groq = "llama-3.1-70b-versatile"
model_name_openai = "gpt-4o-2024-08-06"

llm_openai = ChatOpenAI(
    model=model_name_openai, # 100% json output
    temperature=0,
)

llm_groq = ChatGroq(
    model=model_name_groq, 
    temperature=0,
)

system_prompt = """

Você é um assistente de nutrição que auxilia na listagem de alimentos dado um texto que descreve uma imagem. Registre em uma lista absolutamente todas as comidas presentes no texto.

"""

prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt), 
            ("human", "Descrição da imagem: \n\n {description}")
        ]
)

class FoodList(BaseModel):
    """Gere uma lista de alimentos presentes no texto."""
    
    resultado: List[str] = Field(description="Lista de alimentos presentes na descrição da cena.", 
                                 examples=[["Banana", "Maçã", "Pão", "Queijo"],
                                           ["Arroz", "Feijão", "Carne", "Salada"]])
    

llm_openai_with_tools_extraction = llm_openai.bind_tools([FoodList]) #, strict=True)
llm_groq_with_tools_extraction = llm_groq.with_structured_output(FoodList)

chain_openai_structured_extraction = prompt | llm_openai_with_tools_extraction
chain_groq_structured_extraction = prompt | llm_groq_with_tools_extraction


def get_structured_foods(path: str, provider="openai"):
    image_url = path # "https://www.qgjeitinhocaseiro.com/wp-content/uploads/2019/12/comida-f%C3%A1cil.jpg"
    image_data = base64.b64encode(httpx.get(image_url).content).decode("utf-8")
    message = HumanMessage(
        content=[
            {"type": "text", "text": "Liste em texto absolutamente todas as comidas na imagem."},
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
            },
        ]
    )
    
    response = llm_openai.invoke([message])
    response_content = response.content
    
    if provider == "openai":
        response_struct = chain_openai_structured_extraction.invoke({"description": response_content})
        try:
            output_struct = response_struct.tool_calls[0]['args']['resultado']
        except:
            output_struct = []
    elif provider == "groq":
        response_struct = chain_groq_structured_extraction.invoke({"description": response_content})
        try:
            output_struct = response_struct.resultado
        except:
            output_struct = []

    return output_struct
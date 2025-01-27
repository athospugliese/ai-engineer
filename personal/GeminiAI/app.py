from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
from crewai import Agent, Task, Crew
from crewai import LLM
import litellm
import google.generativeai as genai
import warnings
warnings.filterwarnings("ignore", category=UserWarning,
                        module="pydantic._internal._config")

# Carregar variáveis do .env
load_dotenv()

# Configuração da API Key
API_KEY = os.getenv('GEMINI_AI_API_KEY')
genai.configure(api_key=API_KEY)
litellm.api_key = API_KEY

# Configuração do LLM
llm = LLM(
    model="gemini/gemini-pro",
    temperature=0.7,
    google_api_key=API_KEY,
    tools='google_search_retrieval',
)

# Inicializando o FastAPI
app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ou especifique domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def read_root():
    return {"message": "API funcionando!"}

# Funções auxiliares


def prep_image(image_file):
    """
    Faz o upload da imagem para o Gemini e retorna o objeto do arquivo.
    """
    sample_file = genai.upload_file(
        path=image_file,
        display_name="Nutrition Label"
    )
    return sample_file


def extract_text_from_image(image_file, prompt):
    """
    Realiza o OCR da imagem e retorna o texto extraído.
    """
    model = genai.GenerativeModel(model_name="gemini-1.5-pro")
    response = model.generate_content([image_file.uri, prompt])
    return response.text


def analyze_nutrition_label(label_text):
    """
    Processa o texto do rótulo nutricional com o agente e retorna a análise como dicionário.
    """
    nutritionist_agent = Agent(
        role="Nutricionista",
        goal="Analisar um rótulo nutricional e fornecer uma análise detalhada dos pontos positivos e negativos em tópicos.",
        verbose=True,
        memory=True,
        backstory=(
            "Você é um nutricionista experiente. Sua tarefa é analisar o texto fornecido de um rótulo nutricional, "
            "identificar seus benefícios e potenciais riscos à saúde, e apresentar um resumo claro em tópicos."
        ),
        llm=llm,
    )

    nutrition_task = Task(
        description=(
            "Leia o texto do rótulo nutricional fornecido e analise seus pontos positivos e negativos. "
            "Forneça uma lista clara e detalhada dos prós e contras relacionados aos valores nutricionais, ingredientes e outros aspectos importantes."
        ),
        expected_output="Uma lista enumerada de 1 a 5 em tópicos com os pontos positivos e negativos relacionadas ao produto.",
        agent=nutritionist_agent,
    )

    crew = Crew(
        agents=[nutritionist_agent],
        tasks=[nutrition_task],
        verbose=True
    )

    inputs_array = {'topic': label_text}
    crew_output = crew.kickoff(inputs=inputs_array)

    # Convertendo o resultado para algo serializável em JSON
    result_text = str(crew_output)

    # Processar o texto para separar pontos positivos e negativos
    positive_start = "**Pontos Positivos:**"
    negative_start = "**Pontos Negativos:**"

    positives = ""
    negatives = ""

    if positive_start in result_text and negative_start in result_text:
        positives = result_text.split(positive_start)[
            1].split(negative_start)[0].strip()
        negatives = result_text.split(negative_start)[1].strip()

    # Remover os asteriscos e formatar
    positives = positives.replace("*", "").strip()
    negatives = negatives.replace("*", "").strip()

    result = {
        "task_description": nutrition_task.description,
        "positives": positives,
        "negatives": negatives
    }
    return result

# Endpoint da API


@app.post("/analyze-nutrition-label")
async def analyze_label(file: UploadFile = File(...)):
    """
    Endpoint para receber a imagem, realizar OCR e análise nutricional.
    """
    try:
        # Salvar imagem temporariamente
        file_bytes = await file.read()
        temp_image_path = "temp_image.jpg"
        with open(temp_image_path, "wb") as temp_image:
            temp_image.write(file_bytes)

        # Processar imagem com Gemini
        uploaded_file = prep_image(temp_image_path)
        ocr_prompt = "Extract the text in the image verbatim"
        extracted_text = extract_text_from_image(uploaded_file, ocr_prompt)

        if not extracted_text:
            raise HTTPException(
                status_code=400, detail="Falha ao extrair texto da imagem.")

        # Analisar texto extraído
        analysis = analyze_nutrition_label(extracted_text)

        # Retornar resultado como JSON
        return JSONResponse(
            content={
                "extracted_text": extracted_text,
                "positives": analysis["positives"],
                "negatives": analysis["negatives"]
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Erro ao processar imagem: {str(e)}")
    finally:
        # Remover o arquivo temporário
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)

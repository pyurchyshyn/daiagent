import os
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import pandas as pd
import io

app = FastAPI()

static_path = os.path.abspath("static")
templates_path = os.path.abspath("templates")

print(f"Absolute path to static directory: {static_path}")
print(f"Does static directory exist? {os.path.exists(static_path)}")


app.mount("/static", StaticFiles(directory=static_path), name="static")
templates = Jinja2Templates(directory=templates_path)

# In-memory storage for the dataframe
df = None

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    global df
    filename = file.filename
    if not (filename.endswith(".csv") or filename.endswith(".xls") or filename.endswith(".xlsx")):
        return JSONResponse(content={"error": "Unsupported file format"}, status_code=400)

    try:
        contents = await file.read()
        if filename.endswith(".csv"):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        else:
            df = pd.read_excel(io.BytesIO(contents))

        if df.empty:
            df = None
            return JSONResponse(content={"error": "The uploaded file is empty or malformed."}, status_code=400)

        return JSONResponse(content={"message": f"Successfully uploaded and parsed {filename}"})
    except Exception as e:
        df = None
        return JSONResponse(content={"error": f"Failed to parse file: {e}"}, status_code=500)

@app.post("/ask")
async def ask(request: Request):
    if df is None:
        return JSONResponse(content={"error": "Please upload a file first."}, status_code=400)

    data = await request.json()
    question = data.get("question")
    if not question:
        return JSONResponse(content={"error": "No question provided."}, status_code=400)

    # Simple prompt for the LLM
    prompt = f"""
    You are an AI assistant that can answer questions about an uploaded data table.
    The table has the following columns: {', '.join(df.columns)}.
    When the user asks about the total number of items, total amount, or aggregate quantity, always use SUM(column_name).  
    When the user asks about how many different items or records, use COUNT(*).  
    For example, "How many electronics items in stock?" means total stock units — use SUM(Stock).
    Here are the first 5 rows of the data:
    {df.head().to_string()}

    Question: {question}

    Based on the table, please provide a concise answer to the question. If possible, also provide a SQL query that could be used to answer the question.
    Your response should be in JSON format with two keys: "answer" and "sql_query".
    When the user asks for aggregated values grouped by categories (e.g., average sales by region), always:

    1. Provide a clear, human-readable summary listing the aggregate value for each group separately.
    2. Format numbers with commas or appropriate separators for readability.
    3. Use complete sentences or bullet points to list each group and its corresponding value.
    4. Also provide the correct SQL query that calculates this aggregation, including GROUP BY clause.
    5. If the user asks about totals or counts, use SUM or COUNT accordingly.
    6. When referring to time periods or filters (e.g., sales in June), always apply the appropriate WHERE clause in the SQL.

    Example output:

    "The average sales in June by region were:
    - North: $12,000
    - South: $15,000
    - West: $10,000
    - East: $18,000

    SQL query:
    SELECT Region, AVG(Sales) AS Average_Sales
    FROM table_name
    WHERE Month = 'June'
    GROUP BY Region;"
    """

    try:
        # NOTE: You need to have your OPENAI_API_KEY set as an environment variable
        from openai import OpenAI
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that provides answers based on data tables and generates SQL queries."},
                {"role": "user", "content": prompt}
            ],
            # response_format={"type": "json_object"} # This is only available in newer models
        )
        # It's better to parse the string response to a JSON object
        import json
        content = response.choices[0].message.content
        # A simple way to extract json from the response string
        json_response_str = content[content.find('{'):content.rfind('}')+1]
        model_response = json.loads(json_response_str)


        return JSONResponse(content=model_response)
    except Exception as e:
        return JSONResponse(content={"error": f"Error with AI model: {e}"}, status_code=500)

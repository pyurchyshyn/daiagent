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

    # Формуємо підказку для LLM тільки з перших 5 рядків
    prompt = f"""
    You are an AI assistant that can answer questions about an uploaded data table.
    The table has the following columns: {', '.join(df.columns)}.
    When the user asks about the total number of items, total amount, or aggregate quantity, always use SUM(column_name).
    When the user asks about how many different items or records, use COUNT(*).
    For example, "How many electronics items in stock?" means total stock units — use SUM(Stock).
    Here are the first 5 rows of the data:
    {df.head(5).to_string()}

    Question: {question}

    Please respond in JSON with two keys:
    - "summary": human-friendly answer
    - "sql_query": the SQL query to get the full result from the table

    Always use 'df' as the table name in the SQL query.
    """

    try:
        from openai import OpenAI
        import json
        from pandasql import sqldf

        pysqldf = lambda q: sqldf(q, {"df": df})

        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers based on a pandas DataFrame and generates SQL queries."},
                {"role": "user", "content": prompt}
            ]
        )

        content = response.choices[0].message.content

        # Витягуємо JSON з відповіді
        json_response_str = content[content.find('{'):content.rfind('}')+1]
        model_response = json.loads(json_response_str)

        # Замінюємо table_name на df, якщо модель забула
        sql_query = model_response["sql_query"].replace("table_name", "df")

        # Виконуємо SQL і повертаємо повний результат
        try:
            sql_result_df = pysqldf(sql_query)
            full_result = sql_result_df.to_dict(orient="records")
        except Exception as e:
            return JSONResponse(content={"error": f"SQL execution error: {e}"}, status_code=500)

        return JSONResponse(content={
            "summary": model_response["summary"],
            "sql_query": sql_query,
            "full_result": full_result
        })

    except Exception as e:
        return JSONResponse(content={"error": f"Error with AI model: {e}"}, status_code=500)
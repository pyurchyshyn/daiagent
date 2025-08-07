# AI Assistant for Excel/CSV Tables

This project is a simple AI assistant that allows you to interact with your Excel or CSV tables using natural language. You can upload a file, and then ask questions about the data in a chat interface. The assistant uses an LLM to understand your questions and provide answers, along with the corresponding SQL query if applicable.

## Architecture

The application is built with Python and FastAPI, and the frontend is a simple HTML, CSS, and JavaScript interface. The entire application is self-contained in a single project.

- **Backend**: FastAPI handles the file uploads and the chat logic. It uses `pandas` to parse the uploaded files and `openai` to interact with the LLM.
- **Frontend**: The frontend is a simple chat interface built with HTML, CSS, and vanilla JavaScript. It is served directly by the FastAPI backend.
- **LLM**: The application uses an LLM (e.g., GPT-4) to process natural language questions and generate answers and SQL queries.

## How to run the application

1.  **Clone the repository**
    ```bash
    git clone https://github.com/pyurchyshyn/daiagent.git
    cd daiagent
    ```

2.  **Install the dependencies**
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    ```

3.  **Set your OpenAI API key**
    You need to have an OpenAI API key to use this application. Set it as an environment variable:
    ```bash
    set OPENAI_API_KEY='your-api-key'
    ```

4.  **Run the application**
    ```bash
    uvicorn main:app --reload
    ```

5.  **Open the application in your browser**
    Navigate to `http://127.0.0.1:8000` in your web browser.

## Example Prompts

Once you have uploaded a file, you can ask questions like:

- "What is the average value of the 'Sales' column?"
- "How many rows are there in the table?"
- "Show me the top 5 rows with the highest 'Profit'."
- "What is the total 'Revenue' for the 'North' region?"

The assistant will provide a natural language answer and, if possible, the SQL query used to generate the answer.

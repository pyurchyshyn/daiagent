document.addEventListener("DOMContentLoaded", () => {
    const chatBox = document.getElementById("chat-box");
    const userInput = document.getElementById("user-input");
    const sendButton = document.getElementById("send-button");
    const fileInput = document.getElementById("file-input");
    const uploadButton = document.getElementById("upload-button");


    sendButton.addEventListener("click", sendMessage);
    userInput.addEventListener("keypress", (e) => {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    uploadButton.addEventListener("click", uploadFile);

    function sendMessage() {
        const message = userInput.value;
        if (message.trim() === "") return;

        appendMessage("user", message);
        userInput.value = "";

        fetch("/ask", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ question: message }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                appendMessage("assistant", `Error: ${data.error}`);
            } else {
                appendMessage("assistant", data.summary || "No summary provided.");
                if (data.sql_query) {
                    appendQuery(data.sql_query);
                }
                if (data.full_result) {
                    appendFullResult(data.full_result);
                }
            }
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("assistant", "Sorry, something went wrong.");
        });
    }

    function uploadFile() {
        const file = fileInput.files[0];
        if (!file) {
            appendMessage("assistant", "Please select a file to upload.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        fetch("/upload", {
            method: "POST",
            body: formData,
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                appendMessage("assistant", `Error: ${data.error}`);
            } else {
                appendMessage("assistant", data.message);
            }
        })
        .catch(error => {
            console.error("Error:", error);
            appendMessage("assistant", "Sorry, something went wrong during file upload.");
        });
    }

    function appendMessage(sender, message) {
        const messageElement = document.createElement("div");
        messageElement.classList.add("message", `${sender}-message`);
        messageElement.innerText = message;
        chatBox.appendChild(messageElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function appendQuery(query) {
        const queryElement = document.createElement("div");
        queryElement.classList.add("sql-query");
        queryElement.innerText = query;
        chatBox.appendChild(queryElement);
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    function appendFullResult(results) {
        const container = document.createElement("div");
        container.classList.add("full-result");

        if (Array.isArray(results) && results.length > 0) {
            const table = document.createElement("table");
            table.classList.add("result-table");
            const thead = document.createElement("thead");
            const tbody = document.createElement("tbody");

            // Заголовки таблиці - ключі першого об'єкта
            const headerRow = document.createElement("tr");
            Object.keys(results[0]).forEach(key => {
                const th = document.createElement("th");
                th.innerText = key;
                headerRow.appendChild(th);
            });
            thead.appendChild(headerRow);

            // Рядки таблиці
            results.forEach(row => {
                const tr = document.createElement("tr");
                Object.values(row).forEach(value => {
                    const td = document.createElement("td");
                    td.innerText = value;
                    tr.appendChild(td);
                });
                tbody.appendChild(tr);
            });

            table.appendChild(thead);
            table.appendChild(tbody);
            container.appendChild(table);
        } else {
            container.innerText = "No detailed results to display.";
        }

        chatBox.appendChild(container);
        chatBox.scrollTop = chatBox.scrollHeight;
    }
});

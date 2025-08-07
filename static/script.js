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
                appendMessage("assistant", data.answer);
                if (data.sql_query) {
                    appendQuery(data.sql_query);
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
});

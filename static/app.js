let lastStressScore = null;
let lastTopic = null;

/* ================= RESPONSE ROTATION INDEX ================= */
let responseIndex = {
    sleep: 0,
    study: 0,
    gpa: 0,
    exercise: 0,
    motivate: 0,
    lifestyle: 0
};

/* ================= CHATBOT TOGGLE ================= */
function toggleChatbot() {
    document.getElementById("chatbotPanel").classList.toggle("show");
}

/* ================= SMART AI CHATBOT ================= */
function sendChat() {
    const input = document.getElementById("chatInput");
    const messages = document.getElementById("chatMessages");

    const userText = input.value.trim();
    if (!userText) return;

    // Safe user message display
    const userDiv = document.createElement("div");
    userDiv.innerHTML = "<strong>You:</strong> ";
    userDiv.appendChild(document.createTextNode(userText));
    messages.appendChild(userDiv);

    input.value = "";
    messages.scrollTop = messages.scrollHeight;

    const reply = generateAIResponse(userText.toLowerCase());

    setTimeout(() => {
        const aiDiv = document.createElement("div");
        aiDiv.innerHTML = "<strong>AI:</strong> ";
        aiDiv.appendChild(document.createTextNode(reply));
        messages.appendChild(aiDiv);
        messages.scrollTop = messages.scrollHeight;
    }, 500);
}

/* ================= RESPONSE ENGINE ================= */
function generateAIResponse(text) {

    if (lastStressScore === null) {
        return "Please predict your stress first so I can give personalized advice.";
    }

    /* ===== CONTINUE PREVIOUS TOPIC ===== */
    if ((text === "more" || text === "next" || text === "another") && lastTopic) {
        return getRotatingResponse(lastTopic);
    }

    /* ===== TOPIC DETECTION ===== */

    if (text.includes("sleep")) {
        lastTopic = "sleep";
        return getRotatingResponse("sleep");
    }

    if (text.includes("study") || text.includes("exam")) {
        lastTopic = "study";
        return getRotatingResponse("study");
    }

    if (text.includes("gpa") || text.includes("marks")) {
        lastTopic = "gpa";
        return getRotatingResponse("gpa");
    }

    if (text.includes("exercise") || text.includes("activity")) {
        lastTopic = "exercise";
        return getRotatingResponse("exercise");
    }

    if (text.includes("motivate") || text.includes("sad")) {
        lastTopic = "motivate";
        return getRotatingResponse("motivate");
    }

    if (text.includes("balance") || text.includes("lifestyle")) {
        lastTopic = "lifestyle";
        return getRotatingResponse("lifestyle");
    }

    /* ===== STRESS LEVEL CHECK ===== */

    if (text.includes("stress level") || text.includes("score")) {
        if (lastStressScore > 60)
            return `Your stress level is HIGH (${lastStressScore}%). Focus on rest and relaxation.`;
        else if (lastStressScore > 30)
            return `Your stress level is MODERATE (${lastStressScore}%). Maintain balance.`;
        else
            return `Your stress level is LOW (${lastStressScore}%). Keep it up!`;
    }

    return "I can help with stress, sleep, study, GPA, exercise, motivation, or lifestyle balance.";
}

/* ================= ROTATING RESPONSE FUNCTION ================= */
function getRotatingResponse(topic) {

    const responses = {
        sleep: [
            "Aim for 7–8 hours of sleep.",
            "Maintain a consistent sleep schedule.",
            "Avoid screens before bedtime.",
            "Create a dark and quiet environment."
        ],

        study: [
            "Use the Pomodoro technique: 25 min study + 5 min break.",
            "Practice active recall and spaced repetition.",
            "Avoid last-minute cramming.",
            "Break large subjects into smaller tasks."
        ],

        gpa: [
            "Consistent revision improves GPA.",
            "Seek help from professors when needed.",
            "Track weak subjects and improve gradually.",
            "Balance academics with self-care."
        ],

        exercise: [
            "30 minutes of daily activity reduces stress.",
            "Even a short walk refreshes your mind.",
            "Stretching improves focus.",
            "Regular workouts boost mood."
        ],

        motivate: [
            "Small progress daily leads to big success.",
            "Your worth is not defined by grades.",
            "It's okay to ask for help.",
            "Focus on progress, not perfection."
        ],

        lifestyle: [
            "Balance study and relaxation time.",
            "Schedule hobbies weekly.",
            "Take short breaks during study.",
            "Maintain strong social connections."
        ]
    };

    const reply = responses[topic][responseIndex[topic]];
    responseIndex[topic] =
        (responseIndex[topic] + 1) % responses[topic].length;

    return reply;
}

/* ================= PREDICT FUNCTION ================= */
async function predictStress() {

    const resultBox = document.getElementById("result-box");

    resultBox.innerHTML = `
        <p>✔ Collecting Data...</p>
        <p>✔ Running AI Model...</p>
    `;

    const data = {
        study: document.getElementById("study").value,
        sleep: document.getElementById("sleep").value,
        activity: document.getElementById("activity").value,
        social: document.getElementById("social").value,
        gpa: document.getElementById("gpa").value
    };

    try {
        const response = await fetch("/predict", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (!response.ok) {
            resultBox.innerHTML = `<p style="color:red">${result.error}</p>`;
            return;
        }

        displayResult(result);

    } catch {
        resultBox.innerHTML = `<p style="color:red">Server error</p>`;
    }
}

/* ================= DISPLAY RESULT ================= */
function displayResult(result) {

    const score = Math.round(result.score);
    lastStressScore = score;

    const degree = score * 3.6;
    const resultBox = document.getElementById("result-box");

    resultBox.innerHTML = `
        <div class="progress-circle" id="circle">
            <span id="counter">0</span>
        </div>

        <h3 style="margin-top:15px;color:${result.color}">
            ${result.level} Stress
        </h3>

        <div style="margin-top:20px;text-align:left;">
            <h4>Recommendations:</h4>
            <ul>
                ${result.recommendations.map(r => `<li>${r}</li>`).join("")}
            </ul>
        </div>
    `;

    const circle = document.getElementById("circle");
    const counter = document.getElementById("counter");

    setTimeout(() => {
        circle.style.background =
            `conic-gradient(${result.color} ${degree}deg, rgba(255,255,255,0.1) ${degree}deg)`;
    }, 300);

    let count = 0;
    const interval = setInterval(() => {
        if (count >= score) {
            clearInterval(interval);
        } else {
            count++;
            counter.innerText = count;
        }
    }, 15);
}
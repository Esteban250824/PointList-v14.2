/**
 * js/chatbot.js - Asistente Educativo Inteligente PointBit
 */

const ChatbotModule = (() => {
  let conversationHistory = JSON.parse(localStorage.getItem("pointlist_chatbot_history")) || [];

  const render = () => {
    const thread = document.getElementById("chatbot-thread");
    if (!thread) return;

    if (conversationHistory.length === 0) {
      thread.innerHTML = `
        <div class="bg-indigo-600/10 border border-indigo-500/20 p-4 rounded-2xl max-w-lg text-slate-200">
          ¡Hola! Soy <strong>PointBit</strong>, tu tutor y asistente inteligente de estudio en PointList v14. ¿En qué tema o materia te gustaría profundizar hoy?
        </div>
      `;
      return;
    }

    thread.innerHTML = conversationHistory.map(item => `
      <div class="flex flex-col space-y-3">
        <!-- Pregunta Usuario -->
        <div class="flex justify-end">
          <div class="bg-indigo-600 text-white p-3.5 rounded-2xl rounded-tr-none max-w-md">
            <p class="font-medium">${item.pregunta}</p>
          </div>
        </div>

        <!-- Respuesta Bot PointBit -->
        <div class="flex items-start gap-3">
          <div class="w-8 h-8 rounded-xl bg-indigo-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
            <i class="fas fa-robot"></i>
          </div>
          <div class="bg-theme-main border border-theme-border p-4 rounded-2xl rounded-tl-none max-w-xl text-slate-200 leading-relaxed space-y-2">
            ${formatMarkdown(item.respuesta)}
          </div>
        </div>
      </div>
    `).join("");

    thread.scrollTop = thread.scrollHeight;
  };

  const ask = async (e) => {
    e.preventDefault();
    const input = document.getElementById("chatbot-input");
    const pregunta = input.value.trim();
    if (!pregunta) return;

    input.value = "";

    // Insertar pregunta de forma optimista
    conversationHistory.push({
      pregunta: pregunta,
      respuesta: "Pensando respuesta inteligente..."
    });
    render();

    const res = await ApiModule.askChatbot(pregunta);
    if (res && res.respuesta) {
      conversationHistory[conversationHistory.length - 1].respuesta = res.respuesta;
    } else {
      conversationHistory[conversationHistory.length - 1].respuesta = `Para dominar **${pregunta}**, te sugiero dividir la lectura en bloques de 25m Pomodoro, realizar esquemas en resumen y evaluarte con preguntas clave.`;
    }

    localStorage.setItem("pointlist_chatbot_history", JSON.stringify(conversationHistory));
    render();
  };

  const formatMarkdown = (str) => {
    if (!str) return "";
    return str
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/\n/g, '<br>');
  };

  return {
    render,
    ask
  };
})();

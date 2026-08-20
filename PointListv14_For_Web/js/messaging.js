/**
 * js/messaging.js - Chat Colaborativo de Estudio
 */

const MessagingModule = (() => {
  let messagesList = JSON.parse(localStorage.getItem("pointlist_messages")) || [
    {
      id: 1,
      sender: "Prof. Carlos Mendoza",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Carlos",
      text: "Recuerden revisar el capítulo 4 de Física para la entrega del viernes.",
      time: "10:30 AM",
      isMine: false
    },
    {
      id: 2,
      sender: "Ana Martínez",
      avatar: "https://api.dicebear.com/7.x/avataaars/svg?seed=Ana",
      text: "¿Alguien tiene los apuntes de la clase de Química sobre termodinámica?",
      time: "11:15 AM",
      isMine: false
    }
  ];

  const render = () => {
    const container = document.getElementById("chat-messages-container");
    if (!container) return;

    container.innerHTML = messagesList.map(m => {
      if (m.isMine) {
        return `
          <div class="flex justify-end">
            <div class="bg-indigo-600 text-white p-3 rounded-2xl rounded-tr-none max-w-sm">
              <p>${m.text}</p>
              <span class="text-[10px] text-indigo-200 block text-right mt-1">${m.time}</span>
            </div>
          </div>
        `;
      } else {
        return `
          <div class="flex items-start gap-3">
            <img src="${m.avatar}" class="w-8 h-8 rounded-full border border-indigo-400">
            <div class="bg-theme-main border border-theme-border p-3 rounded-2xl rounded-tl-none max-w-sm">
              <span class="font-bold text-indigo-400 block mb-0.5 text-[11px]">${m.sender}</span>
              <p class="text-slate-200">${m.text}</p>
              <span class="text-[10px] text-slate-400 block text-right mt-1">${m.time}</span>
            </div>
          </div>
        `;
      }
    }).join("");

    container.scrollTop = container.scrollHeight;
  };

  const sendMessage = (e) => {
    e.preventDefault();
    const input = document.getElementById("chat-input");
    const text = input.value.trim();
    if (!text) return;

    const user = AuthModule.getUser();
    const now = new Date();
    const timeStr = `${now.getHours()}:${now.getMinutes().toString().padStart(2, '0')}`;

    const newMsg = {
      id: Date.now(),
      sender: user ? user.nombre_usuario : "Tú",
      avatar: user ? user.photo_url : "assets/logo.png",
      text: text,
      time: timeStr,
      isMine: true
    };

    messagesList.push(newMsg);
    localStorage.setItem("pointlist_messages", JSON.stringify(messagesList));
    input.value = "";
    render();
  };

  return {
    render,
    sendMessage
  };
})();

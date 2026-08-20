/**
 * js/calendar.js - Calendario & Agenda Académica
 */

const CalendarModule = (() => {
  let eventsList = JSON.parse(localStorage.getItem("pointlist_events")) || [
    { id: 1, titulo: "Examen Parcial de Física", fecha: "2026-08-25", prioridad: "urgente", tipo: "Examen" },
    { id: 2, titulo: "Entrega Proyecto de Química", fecha: "2026-08-28", prioridad: "alta", tipo: "Proyecto" },
    { id: 3, titulo: "Taller de Programación Python", fecha: "2026-08-30", prioridad: "normal", tipo: "Tarea" }
  ];

  const render = () => {
    const container = document.getElementById("calendar-events-list");
    if (!container) return;

    container.innerHTML = eventsList.map(ev => {
      let borderCol = "border-indigo-500/30 bg-indigo-500/10 text-indigo-300";
      let prioBadge = "bg-indigo-600 text-white";

      if (ev.prioridad === "urgente") {
        borderCol = "border-red-500/30 bg-red-500/10 text-red-300";
        prioBadge = "bg-red-600 text-white";
      } else if (ev.prioridad === "alta") {
        borderCol = "border-amber-500/30 bg-amber-500/10 text-amber-300";
        prioBadge = "bg-amber-600 text-white";
      }

      return `
        <div class="p-4 rounded-2xl border ${borderCol} flex items-center justify-between">
          <div class="flex items-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center text-indigo-400 font-bold">
              <i class="fas fa-calendar-day"></i>
            </div>
            <div>
              <h4 class="font-bold text-sm text-slate-100">${ev.titulo}</h4>
              <span class="text-xs text-slate-400"><i class="far fa-clock mr-1"></i> ${ev.fecha}</span>
            </div>
          </div>
          <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase ${prioBadge}">
            ${ev.prioridad}
          </span>
        </div>
      `;
    }).join("");
  };

  const openModal = () => {
    document.getElementById("modal-event").classList.remove("hidden");
  };

  const closeModal = () => {
    document.getElementById("modal-event").classList.add("hidden");
  };

  const saveEvent = (e) => {
    e.preventDefault();
    const title = document.getElementById("modal-event-title").value;
    const date = document.getElementById("modal-event-date").value;

    const newEv = {
      id: Date.now(),
      titulo: title,
      fecha: date,
      prioridad: "normal",
      tipo: "General"
    };

    eventsList.push(newEv);
    localStorage.setItem("pointlist_events", JSON.stringify(eventsList));
    ApiModule.saveEvent(newEv);

    closeModal();
    render();
    HomeModule.render();
  };

  return {
    render,
    openModal,
    closeModal,
    saveEvent,
    getEventsList: () => eventsList
  };
})();

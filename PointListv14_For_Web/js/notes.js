/**
 * js/notes.js - Dashboard de Notas & Gráficas Interactivas (Chart.js)
 */

const NotesModule = (() => {
  let notesList = JSON.parse(localStorage.getItem("pointlist_notes")) || [
    { id: 1, asignatura: "Biología", calificacion: 4.5, fecha: "2026-08-10", comentarios: "Excelente examen parcial" },
    { id: 2, asignatura: "Química", calificacion: 4.7, fecha: "2026-08-12", comentarios: "Laboratorio de soluciones" },
    { id: 3, asignatura: "Informática", calificacion: 5.0, fecha: "2026-08-15", comentarios: "Proyecto Final Web" },
    { id: 4, asignatura: "Matemáticas", calificacion: 3.8, fecha: "2026-08-18", comentarios: "Taller de Cálculo" },
    { id: 5, asignatura: "Física", calificacion: 4.5, fecha: "2026-08-19", comentarios: "Laboratorio Mecánica" }
  ];

  let chartInstance = null;

  const render = () => {
    renderTable();
    updateMetrics();
    renderChart();
  };

  const renderTable = () => {
    const tbody = document.getElementById("notes-table-body");
    if (!tbody) return;

    tbody.innerHTML = notesList.map((n) => {
      const score = parseFloat(n.calificacion);
      let badgeClass = "bg-emerald-500/20 text-emerald-400 border-emerald-500/30";
      let statusText = "Excelente";

      if (score < 3.0) {
        badgeClass = "bg-red-500/20 text-red-400 border-red-500/30";
        statusText = "Bajo";
      } else if (score < 4.0) {
        badgeClass = "bg-amber-500/20 text-amber-400 border-amber-500/30";
        statusText = "Aceptable";
      }

      return `
        <tr class="hover:bg-theme-surface/50 transition-all">
          <td class="p-4 font-bold text-slate-200">${n.asignatura}</td>
          <td class="p-4 font-extrabold text-indigo-400 text-sm">${score.toFixed(1)}</td>
          <td class="p-4">
            <span class="px-2.5 py-1 rounded-full text-[10px] font-bold border ${badgeClass}">
              ${statusText}
            </span>
          </td>
          <td class="p-4 text-slate-400">${n.fecha}</td>
          <td class="p-4 text-slate-400 italic">${n.comentarios || "-"}</td>
        </tr>
      `;
    }).join("");
  };

  const updateMetrics = () => {
    if (notesList.length === 0) return;
    const scores = notesList.map(n => parseFloat(n.calificacion));
    const avg = (scores.reduce((a, b) => a + b, 0) / scores.length).toFixed(2);
    const max = Math.max(...scores).toFixed(2);
    const min = Math.min(...scores).toFixed(2);

    const avgEl = document.getElementById("notes-avg-display");
    const maxEl = document.getElementById("notes-max-display");
    const minEl = document.getElementById("notes-min-display");

    if (avgEl) avgEl.textContent = avg;
    if (maxEl) maxEl.textContent = max;
    if (minEl) minEl.textContent = min;
  };

  const renderChart = () => {
    const canvas = document.getElementById("gradesChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Agrupar calificaciones por asignatura
    const subjectsMap = {};
    notesList.forEach((n) => {
      if (!subjectsMap[n.asignatura]) subjectsMap[n.asignatura] = [];
      subjectsMap[n.asignatura].push(parseFloat(n.calificacion));
    });

    const labels = Object.keys(subjectsMap);
    const data = labels.map(sub => {
      const arr = subjectsMap[sub];
      return (arr.reduce((a, b) => a + b, 0) / arr.length).toFixed(2);
    });

    if (chartInstance) {
      chartInstance.destroy();
    }

    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels: labels,
        datasets: [{
          label: 'Promedio por Asignatura',
          data: data,
          backgroundColor: 'rgba(99, 102, 241, 0.75)',
          borderColor: '#6366F1',
          borderWidth: 2,
          borderRadius: 12
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
          y: {
            min: 0,
            max: 5.0,
            grid: { color: 'rgba(255, 255, 255, 0.05)' },
            ticks: { color: '#94A3B8' }
          },
          x: {
            grid: { display: false },
            ticks: { color: '#94A3B8' }
          }
        },
        plugins: {
          legend: { display: false }
        }
      }
    });
  };

  const openModal = () => {
    document.getElementById("modal-note").classList.remove("hidden");
  };

  const closeModal = () => {
    document.getElementById("modal-note").classList.add("hidden");
  };

  const saveNote = (e) => {
    e.preventDefault();
    const subject = document.getElementById("modal-note-subject").value;
    const val = document.getElementById("modal-note-val").value;
    const desc = document.getElementById("modal-note-desc").value;

    const newNote = {
      id: Date.now(),
      asignatura: subject,
      calificacion: parseFloat(val),
      fecha: new Date().toISOString().split("T")[0],
      comentarios: desc
    };

    notesList.push(newNote);
    localStorage.setItem("pointlist_notes", JSON.stringify(notesList));
    ApiModule.saveNote(newNote);

    closeModal();
    render();
    HomeModule.render();
  };

  return {
    render,
    openModal,
    closeModal,
    saveNote,
    getNotesList: () => notesList
  };
})();

/**
 * js/home.js - Módulo de Inicio / Dashboard Principal
 */

const HomeModule = (() => {
  const render = () => {
    const user = AuthModule.getUser();
    if (!user) return;

    // Actualizar nombre en banner
    const welcomeName = document.getElementById("home-welcome-name");
    if (welcomeName) welcomeName.textContent = user.nombre_usuario || user.name || "Estudiante";

    // Cargar estadísticas
    updateStats();
  };

  const updateStats = () => {
    const notes = NotesModule.getNotesList();
    const events = CalendarModule.getEventsList();

    const gpaVal = document.getElementById("stat-gpa-val");
    const homeGpaBadge = document.getElementById("home-gpa-badge");
    const subjectsVal = document.getElementById("stat-subjects-val");
    const eventsVal = document.getElementById("stat-events-val");

    if (notes && notes.length > 0) {
      const total = notes.reduce((acc, n) => acc + parseFloat(n.calificacion || 0), 0);
      const avg = (total / notes.length).toFixed(1);
      if (gpaVal) gpaVal.textContent = avg;
      if (homeGpaBadge) homeGpaBadge.textContent = `${avg} / 5.0`;

      const subjects = new Set(notes.map(n => n.asignatura));
      if (subjectsVal) subjectsVal.textContent = subjects.size || 4;
    } else {
      if (gpaVal) gpaVal.textContent = "4.5";
      if (homeGpaBadge) homeGpaBadge.textContent = "4.5 / 5.0";
      if (subjectsVal) subjectsVal.textContent = "6";
    }

    if (eventsVal) eventsVal.textContent = events ? events.length : 3;
  };

  return {
    render
  };
})();

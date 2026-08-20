/**
 * js/techniques.js - Temporizador Pomodoro 100% Funcional & Catálogo de Técnicas
 */

const TechniquesModule = (() => {
  let timerInterval = null;
  let isRunning = false;
  let currentMode = "work"; // work (25m), short (5m), long (15m)
  let totalSeconds = 25 * 60;
  let remainingSeconds = 25 * 60;

  const techniquesList = [
    {
      id: "pomodoro",
      title: "Método Pomodoro",
      desc: "Divide tu tiempo en bloques de 25m de trabajo intenso sin interrupciones, seguidos de 5m de descanso.",
      dificultad: "Fácil",
      icon: "fa-stopwatch",
      color: "rose"
    },
    {
      id: "feynman",
      title: "Técnica Feynman",
      desc: "Aprende explicando un concepto en lenguaje extremadamente simple como si le enseñaras a un niño.",
      dificultad: "Media",
      icon: "fa-brain",
      color: "indigo"
    },
    {
      id: "active_recall",
      title: "Active Recall",
      desc: "Ponte a prueba activamente recordando información sin mirar los apuntes.",
      dificultad: "Avanzada",
      icon: "fa-bolt",
      color: "amber"
    },
    {
      id: "leitner",
      title: "Sistema Leitner",
      desc: "Usa tarjetas de memoria (flashcards) clasificadas en cajas según la frecuencia de acierto.",
      dificultad: "Media",
      icon: "fa-layer-group",
      color: "emerald"
    },
    {
      id: "sq3r",
      title: "Método SQ3R",
      desc: "Survey, Question, Read, Recite, Review: Estructura la lectura de textos académicos en 5 pasos.",
      dificultad: "Avanzada",
      icon: "fa-book-open",
      color: "sky"
    }
  ];

  const render = () => {
    updateTimerDisplay();
    renderCatalogue();
  };

  const setMode = (mode) => {
    pauseTimer();
    currentMode = mode;

    document.getElementById("pomo-mode-work").className = mode === "work" ? "px-4 py-2 rounded-xl text-xs font-bold bg-indigo-600 text-white" : "px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-slate-200";
    document.getElementById("pomo-mode-short").className = mode === "short" ? "px-4 py-2 rounded-xl text-xs font-bold bg-emerald-600 text-white" : "px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-slate-200";
    document.getElementById("pomo-mode-long").className = mode === "long" ? "px-4 py-2 rounded-xl text-xs font-bold bg-purple-600 text-white" : "px-4 py-2 rounded-xl text-xs font-bold text-slate-400 hover:text-slate-200";

    const label = document.getElementById("pomo-status-label");

    if (mode === "work") {
      totalSeconds = 25 * 60;
      if (label) label.textContent = "Enfoque Profundo (25m)";
    } else if (mode === "short") {
      totalSeconds = 5 * 60;
      if (label) label.textContent = "Descanso Corto (5m)";
    } else {
      totalSeconds = 15 * 60;
      if (label) label.textContent = "Descanso Largo (15m)";
    }

    remainingSeconds = totalSeconds;
    updateTimerDisplay();
  };

  const toggleTimer = () => {
    if (isRunning) {
      pauseTimer();
    } else {
      startTimer();
    }
  };

  const startTimer = () => {
    if (isRunning) return;
    isRunning = true;

    const btn = document.getElementById("pomo-start-btn");
    if (btn) btn.innerHTML = `<i class="fas fa-pause"></i> Pausar`;

    timerInterval = setInterval(() => {
      if (remainingSeconds > 0) {
        remainingSeconds--;
        updateTimerDisplay();
      } else {
        pauseTimer();
        playAlertSound();
        alert("¡Tiempo completado! Buen trabajo.");
      }
    }, 1000);
  };

  const pauseTimer = () => {
    isRunning = false;
    clearInterval(timerInterval);
    const btn = document.getElementById("pomo-start-btn");
    if (btn) btn.innerHTML = `<i class="fas fa-play"></i> Iniciar`;
  };

  const resetTimer = () => {
    pauseTimer();
    remainingSeconds = totalSeconds;
    updateTimerDisplay();
  };

  const updateTimerDisplay = () => {
    const mins = Math.floor(remainingSeconds / 60);
    const secs = remainingSeconds % 60;
    const formatted = `${mins.toString().padStart(2, "0")}:${secs.toString().padStart(2, "0")}`;

    const display = document.getElementById("pomo-timer-display");
    if (display) display.textContent = formatted;

    // Actualizar anillo SVG
    const ring = document.getElementById("pomo-progress-ring");
    if (ring) {
      const circumference = 691;
      const offset = circumference - (remainingSeconds / totalSeconds) * circumference;
      ring.style.strokeDashoffset = offset;
    }
  };

  const playAlertSound = () => {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      osc.type = "sine";
      osc.frequency.setValueAtTime(587.33, ctx.currentTime); // D5 note
      osc.connect(ctx.destination);
      osc.start();
      osc.stop(ctx.currentTime + 0.5);
    } catch (e) {
      console.log("Audio alert fallback");
    }
  };

  const renderCatalogue = () => {
    const grid = document.getElementById("techniques-grid");
    if (!grid) return;

    grid.innerHTML = techniquesList.map(t => `
      <div class="bg-theme-surface border border-theme-border p-5 rounded-2xl space-y-3 hover:border-indigo-500 transition-all flex flex-col justify-between">
        <div>
          <div class="flex justify-between items-center mb-2">
            <div class="w-10 h-10 rounded-xl bg-indigo-500/20 text-indigo-400 flex items-center justify-center text-lg">
              <i class="fas ${t.icon}"></i>
            </div>
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold bg-theme-main border border-theme-border text-slate-400">
              ${t.dificultad}
            </span>
          </div>
          <h4 class="font-bold text-sm text-slate-100">${t.title}</h4>
          <p class="text-xs text-slate-400 mt-1 leading-relaxed">${t.desc}</p>
        </div>
        <button onclick="TechniquesModule.setMode('work')" class="w-full py-2 bg-indigo-600/10 hover:bg-indigo-600/20 text-indigo-400 font-bold rounded-xl text-xs border border-indigo-500/20 transition-all mt-3">
          Aplicar Técnica
        </button>
      </div>
    `).join("");
  };

  return {
    render,
    setMode,
    toggleTimer,
    resetTimer
  };
})();

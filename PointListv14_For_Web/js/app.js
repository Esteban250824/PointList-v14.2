/**
 * js/app.js - Controlador Principal Single Page Application (SPA Router)
 */

const AppController = (() => {
  let currentView = "home";

  const init = () => {
    // Inicializar sub-módulos
    I18nModule.init();
    AuthModule.init();

    // Manejar evento de hash en URL
    window.addEventListener("hashchange", handleHashChange);
    handleHashChange();

    // Aplicar tema guardado
    const savedTheme = localStorage.getItem("pointlist_theme") || "dark";
    setTheme(savedTheme);
  };

  const handleHashChange = () => {
    const hash = window.location.hash.replace("#", "") || "home";
    navigate(hash);
  };

  const navigate = (viewId) => {
    const validViews = ["home", "notes", "calendar", "techniques", "messaging", "chatbot", "profile"];
    if (!validViews.includes(viewId)) viewId = "home";

    currentView = viewId;

    // Ocultar todas las vistas y mostrar la elegida
    validViews.forEach((v) => {
      const pageEl = document.getElementById(`page-${v}`);
      const navItem = document.getElementById(`nav-item-${v}`);

      if (pageEl) {
        if (v === viewId) {
          pageEl.classList.remove("hidden");
        } else {
          pageEl.classList.add("hidden");
        }
      }

      if (navItem) {
        if (v === viewId) {
          navItem.classList.add("active");
        } else {
          navItem.classList.remove("active");
        }
      }
    });

    // Actualizar título y subtítulo en Header
    const titleEl = document.getElementById("header-page-title");
    const subTitleEl = document.getElementById("header-page-subtitle");

    const titles = {
      home: { title: "Inicio", sub: "Plataforma Educativa Integral" },
      notes: { title: "Notas & Promedio", sub: "Dashboard de Rendimiento Académico" },
      calendar: { title: "Calendario & Agenda", sub: "Gestión de Entregas y Evaluaciones" },
      techniques: { title: "Técnicas & Pomodoro", sub: "Temporizador y Métodos de Estudio" },
      messaging: { title: "Mensajería Chat", en: "Canales de Estudio Colaborativo" },
      chatbot: { title: "PointBit Asistente IA", sub: "Tutoría Educativa Inteligente 24/7" },
      profile: { title: "Mi Perfil", sub: "Configuración de Cuenta y Detalles" }
    };

    if (titleEl && titles[viewId]) titleEl.textContent = titles[viewId].title;
    if (subTitleEl && titles[viewId]) subTitleEl.textContent = titles[viewId].sub;

    // Ejecutar renderizado del módulo correspondiente
    switch (viewId) {
      case "home": HomeModule.render(); break;
      case "notes": NotesModule.render(); break;
      case "calendar": CalendarModule.render(); break;
      case "techniques": TechniquesModule.render(); break;
      case "messaging": MessagingModule.render(); break;
      case "chatbot": ChatbotModule.render(); break;
      case "profile": ProfileModule.render(); break;
    }
  };

  const updateUserInfo = (user) => {
    if (!user) return;
    const sidebarAvatar = document.getElementById("sidebar-user-avatar");
    const sidebarName = document.getElementById("sidebar-user-name");
    const sidebarRole = document.getElementById("sidebar-user-role");
    const headerAvatar = document.getElementById("header-user-avatar");

    if (sidebarAvatar) sidebarAvatar.src = user.photo_url || "assets/logo.png";
    if (headerAvatar) headerAvatar.src = user.photo_url || "assets/logo.png";
    if (sidebarName) sidebarName.textContent = user.nombre_usuario || user.name || "Usuario";
    if (sidebarRole) sidebarRole.textContent = user.rol === "profesor" ? "👨‍🏫 Profesor / Tutor" : "🎓 Estudiante";
  };

  const toggleTheme = () => {
    const currentTheme = document.documentElement.getAttribute("data-theme") || "dark";
    const newTheme = currentTheme === "dark" ? "light" : "dark";
    setTheme(newTheme);
  };

  const setTheme = (theme) => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("pointlist_theme", theme);

    const icon = document.getElementById("theme-icon");
    if (icon) {
      icon.className = theme === "dark" ? "fas fa-sun text-amber-400 text-lg" : "fas fa-moon text-slate-700 text-lg";
    }
  };

  const toggleSidebar = () => {
    const sidebar = document.getElementById("sidebar");
    if (sidebar) sidebar.classList.toggle("-translate-x-full");
  };

  return {
    init,
    navigate,
    updateUserInfo,
    toggleTheme,
    toggleSidebar
  };
})();

// Inicializar la aplicación cuando el DOM esté listo
document.addEventListener("DOMContentLoaded", () => {
  AppController.init();
});

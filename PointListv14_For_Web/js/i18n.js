/**
 * js/i18n.js - Sistema de Internacionalización (Multi-idioma) para PointList Web
 * Soporta Español (Latinoamérica), English (US) y Português (Brasil).
 */

const I18nModule = (() => {
  let currentLanguage = localStorage.getItem("pointlist_lang") || "es";

  const translations = {
    // Navegación
    nav_home: { es: "Inicio", en: "Home", pt: "Início" },
    nav_notes: { es: "Notas & Promedio", en: "Grades & GPA", pt: "Notas e Média" },
    nav_calendar: { es: "Calendario & Agenda", en: "Calendar & Schedule", pt: "Calendário e Agenda" },
    nav_techniques: { es: "Técnicas de Estudio", en: "Study Techniques", pt: "Técnicas de Estudo" },
    nav_messaging: { es: "Mensajería Chat", en: "Collaborative Chat", pt: "Chat Colaborativo" },
    nav_chatbot: { es: "PointBit Asistente IA", en: "PointBit AI Assistant", pt: "PointBit Assistente IA" },
    nav_profile: { es: "Mi Perfil", en: "My Profile", pt: "Meu Perfil" },
    nav_logout: { es: "Cerrar Sesión", en: "Log Out", pt: "Sair" },

    // Auth
    login_title: { es: "Iniciar Sesión", en: "Log In", pt: "Entrar" },
    register_title: { es: "Registrarse", en: "Sign Up", pt: "Cadastrar-se" },
    email_label: { es: "Correo Electrónico", en: "Email Address", pt: "E-mail" },
    password_label: { es: "Contraseña", en: "Password", pt: "Senha" },
    remember_me: { es: "Mantener sesión iniciada", en: "Remember me", pt: "Lembrar de mim" },
    forgot_password: { es: "¿Olvidaste tu contraseña?", en: "Forgot password?", pt: "Esqueceu a senha?" },
    btn_login: { es: "Ingresar a PointList", en: "Enter PointList", pt: "Entrar no PointList" },
    btn_create_account: { es: "Crear Cuenta Gratis", en: "Create Free Account", pt: "Criar Conta Grátis" },
    fullname_label: { es: "Nombre Completo", en: "Full Name", pt: "Nome Completo" },
    role_label: { es: "Rol en la Plataforma", en: "Role in Platform", pt: "Função na Plataforma" },

    // KPIs Dashboard
    stat_subjects: { es: "Asignaturas En Curso", en: "Active Subjects", pt: "Disciplinas Ativas" },
    stat_average: { es: "Promedio General", en: "GPA Average", pt: "Média Geral" },
    stat_tasks: { es: "Tareas Completadas", en: "Completed Tasks", pt: "Tarefas Concluídas" },
    stat_events: { es: "Próximos Eventos", en: "Upcoming Events", pt: "Próximos Eventos" },

    // General UI
    btn_save: { es: "Guardar Cambios", en: "Save Changes", pt: "Salvar Alterações" },
    btn_cancel: { es: "Cancelar", en: "Cancel", pt: "Cancelar" }
  };

  const setLanguage = (lang) => {
    if (!["es", "en", "pt"].includes(lang)) lang = "es";
    currentLanguage = lang;
    localStorage.setItem("pointlist_lang", lang);
    applyTranslations();
  };

  const getTranslation = (key) => {
    if (translations[key] && translations[key][currentLanguage]) {
      return translations[key][currentLanguage];
    }
    return key;
  };

  const applyTranslations = () => {
    document.querySelectorAll("[data-i18n]").forEach((element) => {
      const key = element.getAttribute("data-i18n");
      const translated = getTranslation(key);
      if (translated) {
        element.textContent = translated;
      }
    });

    const select = document.getElementById("language-select");
    if (select) select.value = currentLanguage;
  };

  const init = () => {
    applyTranslations();
  };

  return {
    init,
    setLanguage,
    t: getTranslation,
    getLanguage: () => currentLanguage
  };
})();

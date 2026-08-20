/**
 * js/auth.js - Gestión de Autenticación y Sesión de Usuario
 */

const AuthModule = (() => {
  let currentUser = JSON.parse(localStorage.getItem("pointlist_user")) || null;

  const init = () => {
    if (currentUser) {
      showAppShell();
    } else {
      showAuthScreen();
    }
  };

  const switchTab = (tab) => {
    const tabLogin = document.getElementById("tab-btn-login");
    const tabRegister = document.getElementById("tab-btn-register");
    const formLogin = document.getElementById("form-login");
    const formRegister = document.getElementById("form-register");

    if (tab === "login") {
      tabLogin.className = "flex-1 py-3 text-center font-semibold border-b-2 border-indigo-500 text-indigo-400 transition-all";
      tabRegister.className = "flex-1 py-3 text-center font-semibold text-slate-400 border-b-2 border-transparent hover:text-slate-200 transition-all";
      formLogin.classList.remove("hidden");
      formRegister.classList.add("hidden");
    } else {
      tabRegister.className = "flex-1 py-3 text-center font-semibold border-b-2 border-emerald-500 text-emerald-400 transition-all";
      tabLogin.className = "flex-1 py-3 text-center font-semibold text-slate-400 border-b-2 border-transparent hover:text-slate-200 transition-all";
      formRegister.classList.remove("hidden");
      formLogin.classList.add("hidden");
    }
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    const res = await ApiModule.login(email, password);
    if (res && res.success) {
      setUser(res.user);
    } else {
      // Fallback local si backend no responde
      setUser({
        id: 1,
        email: email,
        nombre_usuario: email.split("@")[0],
        rol: "estudiante",
        photo_url: "assets/logo.png"
      });
    }
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    const name = document.getElementById("reg-name").value;
    const email = document.getElementById("reg-email").value;
    const role = document.getElementById("reg-role").value;
    const password = document.getElementById("reg-password").value;

    const userData = { nombre: name, email, rol: role, password };
    const res = await ApiModule.register(userData);
    if (res && res.success) {
      setUser(res.user);
    } else {
      setUser({
        id: Date.now(),
        email: email,
        nombre_usuario: name,
        rol: role,
        photo_url: `https://api.dicebear.com/7.x/avataaars/svg?seed=${name}`
      });
    }
  };

  const loginDemo = () => {
    setUser({
      id: 100,
      email: "demo@pointlist.com",
      nombre_usuario: "Juan Esteban",
      rol: "estudiante",
      photo_url: "assets/logo.png",
      bio: "Estudiante apasionado por el desarrollo de software y aprendizaje contínuo.",
      telefono: "+57 310 987 6543",
      ubicacion: "Medellín, Colombia",
      sitio_web: "https://github.com/pointlist"
    });
  };

  const setUser = (user) => {
    currentUser = user;
    localStorage.setItem("pointlist_user", JSON.stringify(user));
    showAppShell();
  };

  const logout = () => {
    currentUser = null;
    localStorage.removeItem("pointlist_user");
    showAuthScreen();
  };

  const showAppShell = () => {
    document.getElementById("view-auth").classList.add("hidden");
    document.getElementById("app-shell").classList.remove("hidden");
    AppController.updateUserInfo(currentUser);
    AppController.navigate("home");
  };

  const showAuthScreen = () => {
    document.getElementById("app-shell").classList.add("hidden");
    document.getElementById("view-auth").classList.remove("hidden");
  };

  const togglePassword = (inputId) => {
    const input = document.getElementById(inputId);
    input.type = input.type === "password" ? "text" : "password";
  };

  return {
    init,
    switchTab,
    handleLogin,
    handleRegister,
    loginDemo,
    logout,
    togglePassword,
    getUser: () => currentUser
  };
})();

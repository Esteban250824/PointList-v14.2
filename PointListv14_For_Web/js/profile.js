/**
 * js/profile.js - Perfil de Usuario & Ajustes
 */

const ProfileModule = (() => {
  const render = () => {
    const user = AuthModule.getUser();
    if (!user) return;

    const avatarImg = document.getElementById("profile-avatar-img");
    const nameVal = document.getElementById("profile-name-val");
    const roleVal = document.getElementById("profile-role-val");
    const bioInput = document.getElementById("profile-bio-input");
    const phoneInput = document.getElementById("profile-phone-input");

    if (avatarImg) avatarImg.src = user.photo_url || "assets/logo.png";
    if (nameVal) nameVal.textContent = user.nombre_usuario || user.name || "Usuario";
    if (roleVal) roleVal.textContent = user.rol === "profesor" ? "👨‍🏫 Profesor / Tutor" : "🎓 Estudiante";
    if (bioInput) bioInput.value = user.bio || "Estudiante apasionado por la tecnología.";
    if (phoneInput) phoneInput.value = user.telefono || "+57 300 123 4567";
  };

  const saveProfile = () => {
    const user = AuthModule.getUser();
    if (!user) return;

    const bioInput = document.getElementById("profile-bio-input");
    const phoneInput = document.getElementById("profile-phone-input");

    if (bioInput) user.bio = bioInput.value;
    if (phoneInput) user.telefono = phoneInput.value;

    localStorage.setItem("pointlist_user", JSON.stringify(user));
    alert("¡Perfil actualizado con éxito!");
    render();
  };

  return {
    render,
    saveProfile
  };
})();

document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".nav-toggle");
    const nav = document.querySelector(".main-nav");
    if (toggle && nav) toggle.addEventListener("click", () => nav.classList.toggle("open"));

    document.querySelectorAll(".flash").forEach((el) => {
        setTimeout(() => {
            if (el.isConnected) el.style.opacity = "0";
            setTimeout(() => el.remove(), 250);
        }, 5000);
    });
});

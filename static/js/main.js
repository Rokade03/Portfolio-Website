
// NAVBAR HAMBURGER TOGGLE
document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.querySelector(".menu-toggle");
    const nav = document.querySelector(".nav-links");

    if (!toggle || !nav) return;

    toggle.addEventListener("click", () => {
        toggle.classList.toggle("open");
        nav.classList.toggle("open");
    });

    // close menu when a link is clicked (mobile UX)
    nav.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", () => {
            toggle.classList.remove("open");
            nav.classList.remove("open");
        });
    });
});


// Hero blur on scroll as sections overlap it
window.addEventListener("scroll", () => {
    const hero = document.querySelector(".hero");

    if (window.scrollY > 10) {
        hero.classList.add("blur");
    } else {
        hero.classList.remove("blur");
    }
});

document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("contact-form");
    const status = document.getElementById("contact-status");

    if (form) {
        form.addEventListener("submit", async (e) => {
            e.preventDefault();
            status.textContent = "Sending...";

            const formData = new FormData(form);

            try {
                const response = await fetch(form.action, {
                    method: "POST",
                    body: formData
                });

                const result = await response.json();

                if (result.success) {
                    status.textContent = "Thanks! I'll get back to you soon.";
                    status.classList.add("success");
                    form.reset();
                } else {
                    status.textContent = "Something went wrong.";
                    status.classList.add("error");
                }

            } catch (err) {
                status.textContent = "Network error.";
                status.classList.add("error");
            }
        });
    }
});
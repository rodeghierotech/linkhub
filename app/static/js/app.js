document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".copy-btn").forEach((btn) => {
        btn.addEventListener("click", async () => {
            const url = btn.dataset.shortUrl;
            try {
                await navigator.clipboard.writeText(url);
                const original = btn.textContent;
                btn.textContent = "Copiado!";
                setTimeout(() => {
                    btn.textContent = original;
                }, 1500);
            } catch (err) {
                console.error("Falha ao copiar:", err);
            }
        });
    });
});

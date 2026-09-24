document.addEventListener("DOMContentLoaded", () => {
    document.querySelectorAll(".copy-btn").forEach((button) => {
        button.addEventListener("click", async () => {
            const original = button.textContent;
            try {
                await navigator.clipboard.writeText(button.dataset.shortUrl);
                button.textContent = "Copiado!";
            } catch {
                button.textContent = "Não foi possível copiar";
            }
            window.setTimeout(() => { button.textContent = original; }, 1600);
        });
    });

    document.querySelectorAll("[data-confirm-delete]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (!window.confirm("Excluir este link e todo o histórico de cliques?")) {
                event.preventDefault();
            }
        });
    });

    const canvas = document.querySelector("#clicksChart");
    const series = window.linkshortCharts?.clicks;
    if (canvas && series && window.Chart) {
        new Chart(canvas, {
            type: "line",
            data: {
                labels: series.labels,
                datasets: [{
                    label: "Cliques",
                    data: series.values,
                    borderColor: "#5146e5",
                    backgroundColor: "rgba(81, 70, 229, 0.1)",
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false }, border: { display: false } },
                    y: { beginAtZero: true, ticks: { precision: 0 }, border: { display: false } },
                },
            },
        });
    }
});

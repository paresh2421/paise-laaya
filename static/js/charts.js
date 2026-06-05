let expenseChart;

async function renderChart(month = "") {
  const url = month
    ? `/api/expenses-by-category?month=${month}`
    : "/api/expenses-by-category";
  const response = await fetch(url);
  const data = await response.json();
  const canvasContainer = document.getElementById("chart-container");
  const emptyState = document.getElementById("chart-empty-state");

  if (data.values.length === 0 || data.values.every((v) => v === 0)) {
    canvasContainer.classList.add("hidden");
    emptyState.classList.remove("hidden");
    return;
  } else {
    canvasContainer.classList.remove("hidden");
    emptyState.classList.add("hidden");
  }

  const ctx = document.getElementById("expenseChart");
  if (expenseChart) expenseChart.destroy();

  const isDark = document.documentElement.classList.contains("dark");
  const textColor = isDark ? "#9ca3af" : "#4b5563";
  const borderColor = isDark ? "#1f2937" : "#ffffff";

  expenseChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: data.labels,
      datasets: [
        {
          data: data.values,
          // Keeping your existing nice color palette
          backgroundColor: [
            "#3b82f6",
            "#10b981",
            "#f59e0b",
            "#ef4444",
            "#8b5cf6",
            "#ec4899",
          ],
          borderWidth: isDark ? 2 : 1,
          borderColor: borderColor,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: "right",
          labels: { color: textColor, padding: 20, font: { size: 14 } },
        },
      },
      cutout: "65%", // Makes the doughnut ring slightly thinner and sleeker
    },
  });
}

renderChart();

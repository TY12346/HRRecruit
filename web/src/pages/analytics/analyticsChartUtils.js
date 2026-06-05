export const CHART_COLORS = [
  '#2563eb',
  '#16a34a',
  '#f97316',
  '#dc2626',
  '#7c3aed',
  '#0891b2',
  '#ca8a04',
  '#be123c',
  '#4b5563',
  '#0f766e',
  '#9333ea',
];

export const compactChartOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: { position: 'bottom' },
  },
};

export const barChartOptions = {
  ...compactChartOptions,
  scales: {
    y: {
      beginAtZero: true,
      ticks: { precision: 0 },
    },
  },
};

export const horizontalBarChartOptions = {
  ...barChartOptions,
  indexAxis: 'y',
};

export const chartHeight = { height: 320 };

export function chartFromMap(values, label, titleFormatter = (value) => value) {
  const entries = Object.entries(values ?? {});

  return {
    labels: entries.map(([key]) => titleFormatter(key)),
    datasets: [
      {
        label,
        data: entries.map(([, value]) => value),
        backgroundColor: entries.map((_, index) => CHART_COLORS[index % CHART_COLORS.length]),
      },
    ],
  };
}

export function singleValueBar(label, value, datasetLabel, color = '#2563eb') {
  return {
    labels: [label],
    datasets: [
      {
        label: datasetLabel,
        data: [value ?? 0],
        backgroundColor: color,
      },
    ],
  };
}

export function percentageDoughnut(label, value, color = '#16a34a') {
  const safeValue = Math.min(Math.max(Number(value) || 0, 0), 100);

  return {
    labels: [label, 'Remaining'],
    datasets: [
      {
        label,
        data: [safeValue, 100 - safeValue],
        backgroundColor: [color, '#e5e7eb'],
      },
    ],
  };
}

export function downloadBlob(blob, filename) {
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}

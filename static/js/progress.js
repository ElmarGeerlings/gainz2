let progressChartInstance = null;
let progressRepSlider = null;

function progressCssColor(tokenName) {
    return getComputedStyle(document.documentElement).getPropertyValue(tokenName).trim();
}


function loadWorkoutSets(date, exerciseId) {
    const el = document.createElement('span');
    el.setAttribute('data-date', date);
    el.setAttribute('data-exercise-id', exerciseId);
    sendWsRequest('progress/workout_sets', el).then((res) => {
        const c = res.json_content;
        if (c?.target && c?.html) {
            document.querySelector(c.target).innerHTML = c.html;
        }
    });
}

function refreshProgressPageStats() {
    const periodSelect = document.getElementById('progress-period');
    if (!periodSelect) return;
    sendWsRequest('progress/page_stats', periodSelect).then((res) => {
        const c = res.json_content;
        if (c?.target && c?.html) {
            document.querySelector(c.target).innerHTML = c.html;
        }
    });
}

function refreshProgressPage() {
    refreshProgressPageStats();
    drawProgressChart();
}

function renderChart(canvas, dataPoints, metric) {
    if (typeof Chart !== 'function') return;

    if (progressChartInstance) {
        progressChartInstance.destroy();
        progressChartInstance = null;
    }

    const isVolume = metric === 'volume';
    const primaryColor = progressCssColor('--primary') || '#3b57e8';

    let datasets;
    if (isVolume) {
        datasets = [{
            data: dataPoints.map((p) => ({ x: p.date, y: p.volume != null ? Number(p.volume) : null })),
            borderColor: primaryColor,
            backgroundColor: 'rgba(59, 87, 232, 0.15)',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3,
            spanGaps: true,
        }];
    } else {
        datasets = [{
            data: dataPoints.map((p) => ({ x: p.date, y: p.estimated_1rm != null ? Number(p.estimated_1rm) : null })),
            borderColor: primaryColor,
            backgroundColor: 'rgba(59, 87, 232, 0.15)',
            borderWidth: 2,
            pointRadius: 3,
            tension: 0.3,
            spanGaps: true,
        }];
    }

    const name = isVolume ? 'Volume' : 'Est. 1RM';

    progressChartInstance = new Chart(canvas, {
        type: 'line',
        data: { datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: 'index' },
            onClick(evt, elements) {
                if (!elements.length) return;
                const point = dataPoints[elements[0].index];
                const exerciseId = document.getElementById('progress-exercise')?.value;
                if (!point?.date || !exerciseId) return;
                loadWorkoutSets(point.date, exerciseId);
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    callbacks: {
                        label(context) {
                            const raw = context.raw;
                            const value = raw?.y ?? raw;
                            if (value == null) return `${name}: --`;
                            const n = Number(value);
                            const formatted = Number.isFinite(n) ? n.toFixed(isVolume ? 0 : 1) : value;
                            const suffix = isVolume ? ' kg x reps' : ' kg';
                            return `${name}: ${formatted}${suffix}`;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: 'time',
                    time: { unit: 'day', tooltipFormat: 'MMM d, yyyy', displayFormats: { day: 'MMM d' } },
                    grid: { display: false },
                },
                y: {
                    beginAtZero: isVolume,
                    title: { display: true, text: isVolume ? 'Volume (kg x reps)' : 'Weight (kg)' },
                    grid: { color: 'rgba(0, 0, 0, 0.05)' },
                },
            },
        },
    });
}

function setupRepSlider(repBounds) {
    const wrap = document.getElementById('progress-rep-range-wrap');
    const sliderEl = document.getElementById('progress-rep-slider');
    const minInput = document.getElementById('progress-min-reps');
    const maxInput = document.getElementById('progress-max-reps');
    const display = document.getElementById('rep-range-display');

    if (!repBounds || repBounds.min === repBounds.max) {
        wrap.hidden = true;
        if (progressRepSlider) {
            progressRepSlider.destroy();
            progressRepSlider = null;
        }
        return;
    }

    const boundsChanged = !progressRepSlider
        || Number(sliderEl.noUiSlider?.options?.range?.min) !== repBounds.min
        || Number(sliderEl.noUiSlider?.options?.range?.max) !== repBounds.max;

    if (boundsChanged) {
        if (progressRepSlider) {
            progressRepSlider.destroy();
            progressRepSlider = null;
        }
        progressRepSlider = noUiSlider.create(sliderEl, {
            start: [repBounds.min, repBounds.max],
            connect: true,
            step: 1,
            range: { min: repBounds.min, max: repBounds.max },
        });

        progressRepSlider.on('update', (values) => {
            const lo = Math.round(values[0]);
            const hi = Math.round(values[1]);
            minInput.value = String(lo);
            maxInput.value = String(hi);
            if (lo === repBounds.min && hi === repBounds.max) {
                display.textContent = 'All';
            } else {
                display.textContent = `${lo}–${hi} reps`;
            }
        });

        progressRepSlider.on('change', () => {
            drawProgressChart();
        });
    }

    wrap.hidden = false;
}

function switchProgressMetric(event) {
    const button = event.currentTarget;
    const metric = button.getAttribute('data-metric');
    const hiddenInput = document.getElementById('progress-chart-type');
    if (!metric || !hiddenInput) return;

    hiddenInput.value = metric;

    document.querySelectorAll('.progress-metric-btn').forEach((btn) => {
        btn.classList.remove('btn-primary');
        btn.classList.add('btn-outline');
    });
    button.classList.remove('btn-outline');
    button.classList.add('btn-primary');

    drawProgressChart();
}

function drawProgressChart() {
    const canvas = document.getElementById('progress-chart');
    const emptyEl = document.getElementById('progress-chart-empty');
    const setsDetail = document.getElementById('progress-sets-detail');
    const exerciseId = document.getElementById('progress-exercise')?.value || '';

    if (!exerciseId) {
        canvas.hidden = true;
        emptyEl.textContent = 'Select an exercise to see your progress.';
        emptyEl.hidden = false;
        if (setsDetail) setsDetail.innerHTML = '';
        setupRepSlider(null);
        if (progressChartInstance) {
            progressChartInstance.destroy();
            progressChartInstance = null;
        }
        return;
    }

    const form = document.getElementById('progress-form');
    sendWsRequest('progress/chart_data', form).then((response) => {
        const data = response.json_content?.data || [];
        const repBounds = response.json_content?.rep_bounds || null;

        if (setsDetail) setsDetail.innerHTML = '';
        setupRepSlider(repBounds);

        if (!data.length) {
            canvas.hidden = true;
            emptyEl.textContent = 'No data for this selection.';
            emptyEl.hidden = false;
            if (progressChartInstance) {
                progressChartInstance.destroy();
                progressChartInstance = null;
            }
            return;
        }

        const metric = document.getElementById('progress-chart-type')?.value || '1rm';
        emptyEl.hidden = true;
        canvas.hidden = false;
        renderChart(canvas, data, metric);
    });
}

function initProgressPage() {
    refreshProgressPageStats();
    const exerciseSelect = document.getElementById('progress-exercise');
    if (exerciseSelect && exerciseSelect.value) {
        drawProgressChart();
    }
}

document.addEventListener('DOMContentLoaded', initProgressPage);

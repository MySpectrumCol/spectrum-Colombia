const state = {
  questions: [],
  answers: [],
  current: 0,
  sessionToken: "",
  selfLabel: "NONE",
};

const axisLabels = {
  UD: "Ultraderecha",
  D: "Derecha",
  C: "Centro",
  I: "Izquierda",
  UI: "Ultraizquierda",
  MIXED: "Mixto"
};

// Selectores del DOM
const intro = document.querySelector("#intro");
const test = document.querySelector("#test");
const result = document.querySelector("#result");
const username = document.querySelector("#username");
const selfLabel = document.querySelector("#selfLabel");
const startButton = document.querySelector("#startButton");
const progressText = document.querySelector("#progressText");
const progressBar = document.querySelector("#progressBar");
const questionText = document.querySelector("#questionText");
const options = document.querySelector("#options");

const dominant = document.querySelector("#dominant");
const bars = document.querySelector("#bars");
const summary = document.querySelector("#summary");
const shareText = document.querySelector("#shareText");
const copyButton = document.querySelector("#copyButton");
const downloadButton = document.querySelector("#downloadButton");
const xShare = document.querySelector("#xShare");
const againButton = document.querySelector("#againButton");
const resultCard = document.querySelector("#resultCard");
const cardLine = document.querySelector("#cardLine");

const spectrumMarker = document.querySelector("#spectrumMarker");
const mirrorFeedback = document.querySelector("#mirrorFeedback");
const statsBars = document.querySelector("#statsBars");
const statsTotalParticipants = document.querySelector("#statsTotalParticipants");
const globalStatsContainer = document.querySelector("#globalStatsContainer");
const toggleStatsButton = document.querySelector("#toggleStatsButton");

let latestPayload = null;

function cleanUsername(value) {
  return value.trim().replace(/^@/, "") || `usuario_${Date.now()}`;
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.detail || "No se pudo completar la accion");
  }
  return payload;
}

async function startTest() {
  const userVal = username.value.trim();
  const labelVal = selfLabel.value;
  
  if (!userVal) {
    alert("Por favor, ingresa tu usuario de X (Twitter) o tu correo electrónico para comenzar.");
    username.focus();
    return;
  }

  const xRegex = /^@?[a-zA-Z0-9_]{1,15}$/;
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!xRegex.test(userVal) && !emailRegex.test(userVal)) {
    alert("Formato no válido. Introduce un usuario de X válido (ej: @miusuario) o un correo electrónico (ej: tu@correo.com).");
    username.focus();
    return;
  }

  if (!labelVal) {
    alert("Por favor, selecciona con qué corriente política te identificas.");
    selfLabel.focus();
    return;
  }

  startButton.disabled = true;
  startButton.textContent = "Preparando...";
  try {
    const [questionPayload, sessionPayload] = await Promise.all([
      api("/questions"),
      api("/session", { method: "POST", body: "" }),
    ]);
    state.questions = questionPayload.questions;
    state.sessionToken = sessionPayload.session_token;
    state.answers = [];
    state.current = 0;
    state.selfLabel = labelVal;

    intro.classList.add("hidden");
    result.classList.add("hidden");
    test.classList.remove("hidden");
    
    // Resetear vistas previas de estadísticas
    globalStatsContainer.classList.add("hidden");
    toggleStatsButton.textContent = "Ver Estadísticas Globales";
    
    renderQuestion();
  } catch (error) {
    alert(error.message);
  } finally {
    startButton.disabled = false;
    startButton.textContent = "Empezar test";
  }
}

function renderQuestion() {
  const question = state.questions[state.current];
  progressText.textContent = `Pregunta ${state.current + 1} de ${state.questions.length}`;
  progressBar.style.width = `${((state.current + 1) / state.questions.length) * 100}%`;
  questionText.textContent = question.text;
  options.innerHTML = "";

  Object.entries(question.options).forEach(([letter, text]) => {
    const optDiv = document.createElement("div");
    optDiv.className = "option";
    optDiv.setAttribute("role", "button");
    optDiv.setAttribute("tabindex", "0");
    optDiv.innerHTML = `<span class="letter">${letter}</span><span>${text}</span>`;
    
    const selectHandler = () => answerQuestion(letter);
    optDiv.addEventListener("click", selectHandler);
    optDiv.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        selectHandler();
      }
    });
    options.appendChild(optDiv);
  });
}

async function answerQuestion(letter) {
  state.answers.push(letter);
  if (state.answers.length < state.questions.length) {
    state.current += 1;
    renderQuestion();
    return;
  }

  await submitTest();
}

async function submitTest() {
  test.classList.add("hidden");
  const user = cleanUsername(username.value);
  try {
    const payload = await api("/submit", {
      method: "POST",
      body: JSON.stringify({
        user_id: `${user}_${Date.now()}`,
        username: user,
        session_token: state.sessionToken,
        answers: state.answers,
        self_label: state.selfLabel,
      }),
    });
    
    // Renderizar resultados en pantalla inmediatamente
    renderResult(payload);
    
    // En segundo plano, renderizar la tarjeta en canvas y subirla para compartir en X
    setTimeout(async () => {
      try {
        const canvas = await drawResultCard(payload);
        const base64Image = canvas.toDataURL("image/png");
        const uploadResult = await api(`/result/${payload.user_id}/card`, {
          method: "POST",
          body: JSON.stringify({ card_image: base64Image })
        });
        
        // Actualizar datos del payload en local con el enlace final de la imagen
        payload.card_image_path = uploadResult.card_image_path;
        latestPayload = payload;
        
        // Actualizar link de X para que la tarjeta sea previsualizada directamente
        const shareUrl = `${window.location.origin}/result/${payload.user_id}`;
        const finalShareText = `${payload.share_text} (Intento #${payload.attempt_number})\n\nMira mis respuestas detalladas aquí: ${shareUrl}`;
        xShare.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(finalShareText)}`;
        shareText.value = finalShareText;
      } catch (err) {
        console.error("Error al renderizar o subir tarjeta de imagen:", err);
      }
    }, 150);

  } catch (error) {
    alert(error.message);
    intro.classList.remove("hidden");
  }
}

function renderResult(payload) {
  latestPayload = payload;
  dominant.textContent = payload.dominant;
  cardLine.textContent = `${payload.username} | Intento #${payload.attempt_number} | Spectrum Colombia`;
  summary.textContent = payload.summary;
  mirrorFeedback.innerHTML = payload.mirror_feedback;
  
  // URL por defecto antes de que termine de subir la tarjeta de imagen dinámica
  const shareUrl = `${window.location.origin}/result/${payload.user_id}`;
  const initialShareText = `${payload.share_text} (Intento #${payload.attempt_number})\n\nMira mis respuestas detalladas aquí: ${shareUrl}`;
  shareText.value = initialShareText;
  xShare.href = `https://twitter.com/intent/tweet?text=${encodeURIComponent(initialShareText)}`;
  
  resultCard.className = `result-card axis-${payload.dominant_axis}`;

  // Calcular la posición en la Barra del Espectro
  // Pesos: UD (+100), D (+50), C (0), I (-50), UI (-100)
  const weights = { UD: 100, D: 50, C: 0, I: -50, UI: -100 };
  let totalWeight = 0;
  Object.entries(payload.result).forEach(([axis, value]) => {
    totalWeight += weights[axis] * (value / 100);
  });
  
  // Mapeo: de -100 (Ultraizquierda) a +100 (Ultraderecha) -> de 0% a 100% de ancho
  const markerPercent = (totalWeight + 100) / 200 * 100;
  
  // Animación del marcador: iniciar en el centro y deslizarse
  spectrumMarker.style.left = "50%";
  setTimeout(() => {
    spectrumMarker.style.left = `${markerPercent}%`;
  }, 100);

  // Renderizar barras de porcentaje
  bars.innerHTML = "";
  Object.entries(payload.result).forEach(([axis, value]) => {
    const row = document.createElement("div");
    row.className = "bar";
    row.innerHTML = `
      <span>${axis}</span>
      <span class="track"><span class="fill" style="width:0%"></span></span>
      <span>${value}%</span>
    `;
    row.title = axisLabels[axis];
    bars.appendChild(row);
    
    // Animar las barras individuales
    setTimeout(() => {
      row.querySelector(".fill").style.width = `${value}%`;
    }, 150);
  });

  result.classList.remove("hidden");
}

async function copyShareText() {
  await navigator.clipboard.writeText(shareText.value);
  copyButton.textContent = "Copiado";
  setTimeout(() => {
    copyButton.textContent = "Copiar para X";
  }, 1400);
}

async function drawResultCard(payload) {
  // Asegurar precarga de Outfit de Google Fonts en el canvas
  try {
    await document.fonts.load("bold 26px Outfit");
    await document.fonts.load("bold 72px Outfit");
    await document.fonts.load("500 24px Outfit");
    await document.fonts.load("bold 20px Outfit");
    await document.fonts.load("bold 22px Outfit");
    await document.fonts.load("bold 16px Outfit");
  } catch (e) {
    console.warn("No se pudo pre-cargar Google Font en canvas, usando fuente de sistema", e);
  }

  const canvas = document.createElement("canvas");
  canvas.width = 1200;
  canvas.height = 675;
  const ctx = canvas.getContext("2d");
  
  // Fondo oscuro elegante
  const gradient = ctx.createLinearGradient(0, 0, 1200, 675);
  gradient.addColorStop(0, "#11100f");
  gradient.addColorStop(1, "#1c1b1a");
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, 1200, 675);

  // Barra de color en la base
  const colors = ["#c83f3f", "#d36a24", "#d0a21c", "#2f7d59", "#256f9c"];
  colors.forEach((color, index) => {
    ctx.fillStyle = color;
    ctx.fillRect(index * 240, 650, 240, 25);
  });

  // Panel central traslúcido (glassmorphism)
  ctx.fillStyle = "rgba(255, 255, 255, 0.04)";
  ctx.strokeStyle = "rgba(255, 255, 255, 0.08)";
  ctx.lineWidth = 1;
  
  // Dibujar panel redondeado
  ctx.beginPath();
  ctx.roundRect(60, 60, 1080, 530, 16);
  ctx.fill();
  ctx.stroke();

  // Título de marca
  ctx.fillStyle = "#256f9c";
  ctx.font = "bold 26px Outfit, sans-serif";
  ctx.fillText("SPECTRUM COLOMBIA", 110, 130);

  // Nombre de usuario y etiqueta
  ctx.fillStyle = "#ffffff";
  ctx.font = "bold 72px Outfit, sans-serif";
  ctx.fillText(payload.dominant, 110, 215);

  ctx.fillStyle = "rgba(255, 255, 255, 0.6)";
  ctx.font = "500 24px Outfit, sans-serif";
  const displayUser = payload.username.includes("@") ? payload.username : `@${payload.username}`;
  ctx.fillText(`${displayUser} (Intento #${payload.attempt_number}) | Test de Orientación Política`, 110, 265);

  // Dibujar las barras de porcentaje secundarias (las 5 categorías)
  const entries = Object.entries(payload.result);
  entries.forEach(([axis, value], index) => {
    const y = 350 + index * 42;
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 20px Outfit, sans-serif";
    ctx.fillText(axis, 110, y);
    
    // Carril
    ctx.fillStyle = "rgba(255, 255, 255, 0.08)";
    ctx.beginPath();
    ctx.roundRect(175, y - 17, 300, 16, 8);
    ctx.fill();
    
    // Relleno
    ctx.fillStyle = colors[index];
    ctx.beginPath();
    ctx.roundRect(175, y - 17, Math.max(8, 300 * value / 100), 16, 8);
    ctx.fill();
    
    ctx.fillStyle = "#ffffff";
    ctx.font = "bold 20px Outfit, sans-serif";
    ctx.fillText(`${value}%`, 495, y);
  });

  // Dibujar la Barra Continua del Espectro (Spectrum Bar) en el canvas
  const specX = 640;
  const specY = 380;
  const specW = 400;
  const specH = 22;
  
  // Título del espectro
  ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
  ctx.font = "bold 22px Outfit, sans-serif";
  ctx.fillText("MI POSICIÓN EN EL ESPECTRO", specX, specY - 24);

  // Dibujar degradado continuo
  const specGrad = ctx.createLinearGradient(specX, 0, specX + specW, 0);
  colors.forEach((color, i) => {
    specGrad.addColorStop(i / (colors.length - 1), color);
  });
  ctx.fillStyle = specGrad;
  
  ctx.beginPath();
  ctx.roundRect(specX, specY, specW, specH, 11);
  ctx.fill();

  // Calcular la posición del marcador en base a pesos políticos
  const weights = { UD: 100, D: 50, C: 0, I: -50, UI: -100 };
  let totalWeight = 0;
  Object.entries(payload.result).forEach(([axis, pct]) => {
    totalWeight += weights[axis] * (pct / 100);
  });
  const markerPercent = (totalWeight + 100) / 200;
  const markerX = specX + (markerPercent * specW);

  // Dibujar Marcador
  ctx.fillStyle = "#11100f";
  ctx.strokeStyle = "#ffffff";
  ctx.lineWidth = 5;
  ctx.beginPath();
  ctx.arc(markerX, specY + specH/2, 18, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();

  // Etiquetas de la barra del espectro
  ctx.fillStyle = "rgba(255, 255, 255, 0.5)";
  ctx.font = "bold 16px Outfit, sans-serif";
  ctx.fillText("Ultraizquierda", specX, specY + specH + 26);
  ctx.fillText("Centro", specX + specW/2 - 25, specY + specH + 26);
  ctx.fillText("Ultraderecha", specX + specW - 95, specY + specH + 26);

  // Enlace y footer de virilidad
  ctx.fillStyle = "rgba(255, 255, 255, 0.4)";
  ctx.font = "500 18px Outfit, sans-serif";
  ctx.fillText("spectrum-colombia.com", 110, 560);

  ctx.fillStyle = "rgba(255, 255, 255, 0.8)";
  ctx.font = "bold 18px Outfit, sans-serif";
  ctx.fillText("Descubre tu verdadera corriente política", 640, 560);

  return canvas;
}

async function downloadResultCard() {
  if (!latestPayload) return;
  downloadButton.disabled = true;
  downloadButton.textContent = "Preparando...";
  try {
    const canvas = await drawResultCard(latestPayload);
    const link = document.createElement("a");
    link.download = `spectrum-${latestPayload.username}.png`;
    link.href = canvas.toDataURL("image/png");
    link.click();
  } catch (err) {
    console.error("Error al descargar tarjeta:", err);
  } finally {
    downloadButton.disabled = false;
    downloadButton.textContent = "Descargar tarjeta";
  }
}

async function toggleStats() {
  if (globalStatsContainer.classList.contains("hidden")) {
    globalStatsContainer.classList.remove("hidden");
    toggleStatsButton.textContent = "Ocultar Estadísticas Globales";
    
    try {
      const stats = await api("/stats");
      statsTotalParticipants.textContent = `Total participantes: ${stats.total_participants}`;
      statsBars.innerHTML = "";
      
      const colors = {
        UD: "var(--red)",
        D: "var(--orange)",
        C: "var(--yellow)",
        I: "var(--green)",
        UI: "var(--blue)",
        MIXED: "var(--purple)"
      };
      
      Object.entries(stats.percentages).forEach(([axis, value]) => {
        const row = document.createElement("div");
        row.className = "bar";
        row.innerHTML = `
          <span>${axis}</span>
          <span class="track"><span class="fill" style="width:0%; background: ${colors[axis] || "var(--blue)"}"></span></span>
          <span>${value}%</span>
        `;
        row.title = axisLabels[axis] || axis;
        statsBars.appendChild(row);
        
        // Animar la barra de estadísticas
        setTimeout(() => {
          row.querySelector(".fill").style.width = `${value}%`;
        }, 100);
      });
      
      globalStatsContainer.scrollIntoView({ behavior: "smooth" });
    } catch (err) {
      alert("Error al cargar estadísticas: " + err.message);
    }
  } else {
    globalStatsContainer.classList.add("hidden");
    toggleStatsButton.textContent = "Ver Estadísticas Globales";
  }
}

function reset() {
  result.classList.add("hidden");
  intro.classList.remove("hidden");
}

// Event Listeners
startButton.addEventListener("click", startTest);
copyButton.addEventListener("click", copyShareText);
downloadButton.addEventListener("click", downloadResultCard);
toggleStatsButton.addEventListener("click", toggleStats);
againButton.addEventListener("click", reset);

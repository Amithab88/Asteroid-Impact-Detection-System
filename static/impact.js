(function(){
  const dataEl = document.getElementById('metrics-data');
  if (!dataEl) return; // nothing to draw
  let metrics = {};
  try { metrics = JSON.parse(dataEl.textContent || '{}'); } catch (_) { return; }

  // Horizontal bar chart of effects using Chart.js (if available)
  const chartCanvas = document.getElementById('effectsChart');
  if (chartCanvas && window.Chart) {
    const labels = [
      'Crater diameter',
      'Air blast radius',
      'Shock wave radius',
      'Thermal radiation radius'
    ];
    const values = [metrics.crater_km, metrics.air_km, metrics.shock_km, metrics.thermal_km];
    const explanations = [
      'Crater diameter is local to the impact point and grows sub‑linearly with energy (~E^1/4).',
      'Air blast radius extends far as pressure waves propagate through the atmosphere.',
      'Shock wave radius often exceeds thermal as pressure attenuates slower than heat.',
      'Thermal radiation radius falls off roughly with 1/r² and is absorbed by the air.'
    ];
    const shortExplanations = [
      'Local; grows slowly with energy',
      'Pressure waves travel far',
      'Pressure drops slower than heat',
      'Heat ~1/r² and absorbed by air'
    ];

    const barChart = new Chart(chartCanvas.getContext('2d'), {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Impact effects (km)',
          data: values,
          backgroundColor: [
            'rgba(93,59,141,0.6)',
            'rgba(65,105,225,0.6)',
            'rgba(220,20,60,0.6)',
            'rgba(255,140,0,0.6)'
          ],
          borderColor: [
            'rgba(93,59,141,1.0)',
            'rgba(65,105,225,1.0)',
            'rgba(220,20,60,1.0)',
            'rgba(255,140,0,1.0)'
          ],
          borderWidth: 1
        }]
      },
      options: {
        indexAxis: 'y', // Horizontal bars
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          title: { display: true, text: `Energy: ${metrics.energy_megatons_tnt} Mt | Severity: ${metrics.severity}`, font: { size: 12 } },
          tooltip: {
            displayColors: false,
            padding: 6,
            cornerRadius: 6,
            caretSize: 5,
            bodySpacing: 2,
            titleSpacing: 2,
            titleFont: { size: 11, weight: '700' },
            bodyFont: { size: 10.5, lineHeight: 1.15 },
            callbacks: {
              title: (items) => items?.[0]?.label || '',
              label: (ctx) => ` ${ctx.formattedValue} km`,
              afterLabel: (ctx) => {
                const i = ctx.dataIndex;
                return `\n${shortExplanations[i]}`;
              }
            }
          }
        },
        scales: {
          x: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.08)' }, title: { display: true, text: 'Distance/Size (km)' }, ticks: { font: { size: 10.5 } } },
          y: { ticks: { font: { weight: '600', size: 10.5 } }, title: { display: true, text: 'Effect Type' } }
        }
      }
    });
  }


  // Canvas animation of asteroid impact — simplified + informative overlays
  const canvas = document.getElementById('impactCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  const W = canvas.width;
  const H = canvas.height;
  const groundY = Math.round(H * 0.75);

  // Scale radii to pixels for visual rings
  const maxEffectKm = Math.max(1, metrics.air_km || 0, metrics.shock_km || 0, metrics.thermal_km || 0);
  const maxVisualRadius = Math.min(W, groundY) * 0.45;
  const kmToPx = (km) => (km / maxEffectKm) * maxVisualRadius;

  const rings = [
    { name: 'Thermal', km: metrics.thermal_km || 0, colorFill: 'rgba(255,140,0,0.12)', colorStroke: 'rgba(255,140,0,0.9)' },
    { name: 'Shock',   km: metrics.shock_km   || 0, colorFill: 'rgba(220,20,60,0.10)', colorStroke: 'rgba(220,20,60,0.9)' },
    { name: 'Air',     km: metrics.air_km     || 0, colorFill: 'rgba(65,105,225,0.10)', colorStroke: 'rgba(65,105,225,0.9)' }
  ];

  // Meteor state (faster, simpler)
  const impactX = W * 0.5;
  const impactY = groundY - 2;
  const startX = -40;
  const startY = 20;
  const travelTime = 90; // frames
  let frame = 0;

  // Particle explosion (reduced)
  const particles = [];
  function spawnParticles(n) {
    for (let i = 0; i < n; i++) {
      const angle = Math.random() * Math.PI * 2;
      const speed = 0.8 + Math.random() * 1.8;
      particles.push({
        x: impactX,
        y: impactY,
        vx: Math.cos(angle) * speed,
        vy: Math.sin(angle) * speed,
        life: 40 + Math.random() * 25,
        color: i % 2 ? 'rgba(255,180,0,0.75)' : 'rgba(255,100,0,0.75)'
      });
    }
  }

  // Crater formation particles
  const craterParticles = [];
  function spawnCraterParticles() {
    const craterR = Math.max(2, kmToPx(metrics.crater_km || 0) * 0.5);
    const numParticles = Math.min(120, Math.floor(craterR * 3));
    
    for (let i = 0; i < numParticles; i++) {
      const angle = Math.random() * Math.PI * 2;
      const distance = Math.random() * craterR;
      const x = impactX + Math.cos(angle) * distance;
      const y = impactY + Math.sin(angle) * distance;
      
      // Different particle types
      const particleType = Math.random();
      let color, size, vy;
      
      if (particleType < 0.3) {
        // Large debris
        color = `rgba(${160 + Math.random() * 40}, ${82 + Math.random() * 20}, ${45 + Math.random() * 15}, 0.9)`;
        size = 2 + Math.random() * 3;
        vy = -3 - Math.random() * 4;
      } else if (particleType < 0.7) {
        // Medium dust
        color = `rgba(${139 + Math.random() * 50}, ${69 + Math.random() * 30}, ${19 + Math.random() * 20}, 0.7)`;
        size = 1 + Math.random() * 2;
        vy = -2 - Math.random() * 3;
      } else {
        // Fine particles
        color = `rgba(${205 + Math.random() * 30}, ${133 + Math.random() * 40}, ${63 + Math.random() * 20}, 0.6)`;
        size = 0.5 + Math.random() * 1;
        vy = -1 - Math.random() * 2;
      }
      
      craterParticles.push({
        x: x,
        y: y,
        vx: Math.cos(angle) * (0.8 + Math.random() * 2),
        vy: vy,
        life: 80 + Math.random() * 60,
        size: size,
        color: color,
        type: particleType
      });
    }
  }

  function updateParticles() {
    for (let i = particles.length - 1; i >= 0; i--) {
      const p = particles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.03; // gravity
      p.life -= 1;
      if (p.life <= 0) particles.splice(i, 1);
    }
  }

  function updateCraterParticles() {
    for (let i = craterParticles.length - 1; i >= 0; i--) {
      const p = craterParticles[i];
      p.x += p.vx;
      p.y += p.vy;
      p.vy += 0.06; // adjusted gravity
      p.vx *= 0.99; // reduced air resistance
      
      // Add some turbulence
      if (p.type < 0.3) {
        p.vx += (Math.random() - 0.5) * 0.1;
      }
      
      p.life -= 1;
      if (p.life <= 0) craterParticles.splice(i, 1);
    }
  }

  function drawParticles() {
    particles.forEach(p => {
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, 1.5, 0, Math.PI * 2);
      ctx.fill();
    });
  }

  function drawCraterParticles() {
    craterParticles.forEach(p => {
      // Add glow effect for larger particles
      if (p.type < 0.3) {
        ctx.shadowColor = p.color;
        ctx.shadowBlur = 3;
      }
      
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
      ctx.fill();
      
      // Reset shadow
      ctx.shadowBlur = 0;
    });
  }

  function clear() {
    // Space background
    ctx.fillStyle = '#0f1130';
    ctx.fillRect(0, 0, W, H);
    // Stars (reduced)
    ctx.fillStyle = 'rgba(255,255,255,0.25)';
    for (let i = 0; i < 15; i++) {
      const sx = (i * 83) % W;
      const sy = (i * 57) % Math.floor(H * 0.5);
      ctx.fillRect(sx, sy, 1, 1);
    }
    // Ground
    ctx.fillStyle = '#1a1d3f';
    ctx.fillRect(0, groundY, W, H - groundY);
  }

  function drawMeteor(progress) {
    const x = startX + (impactX - startX) * progress;
    const y = startY + (impactY - startY) * progress;
    
    // Enhanced trail with glow
    ctx.shadowColor = 'rgba(255,200,120,0.8)';
    ctx.shadowBlur = 8;
    ctx.strokeStyle = 'rgba(255,200,120,0.7)';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.moveTo(x - 20, y - 12);
    ctx.lineTo(x, y);
    ctx.stroke();
    
    // Reset shadow
    ctx.shadowBlur = 0;
    
    // Enhanced body with better gradient
    const grad = ctx.createRadialGradient(x, y, 1, x, y, 8);
    grad.addColorStop(0, '#fff5e6');
    grad.addColorStop(0.3, '#ffd27a');
    grad.addColorStop(0.7, '#ff8c00');
    grad.addColorStop(1, '#ff7b00');
    
    ctx.fillStyle = grad;
    ctx.beginPath();
    ctx.arc(x, y, 6, 0, Math.PI * 2);
    ctx.fill();
    
    // Add inner glow
    ctx.fillStyle = 'rgba(255,255,255,0.3)';
    ctx.beginPath();
    ctx.arc(x - 1, y - 1, 2, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawRings(expansion) {
    // expansion 0..1 with smooth easing
    const easedExpansion = 1 - Math.pow(1 - expansion, 3); // easeOut cubic
    
    rings.forEach((r, index) => {
      const targetR = kmToPx(r.km);
      const currentR = targetR * easedExpansion;
      
      // Add pulsing effect when rings reach final size
      let pulseEffect = 1;
      if (expansion >= 0.95) {
        const pulsePhase = (expansion - 0.95) * 20; // 0 to 1 over last 5%
        pulseEffect = 1 + Math.sin(pulsePhase * Math.PI * 4) * 0.1; // 10% pulse
      }
      
      const finalR = currentR * pulseEffect;
      
      // Enhanced ring styling with glow
      ctx.shadowColor = r.colorStroke;
      ctx.shadowBlur = expansion > 0.8 ? 8 : 4;
      
      ctx.fillStyle = r.colorFill;
      ctx.strokeStyle = r.colorStroke;
      ctx.lineWidth = expansion > 0.8 ? 2.5 : 1.5;
      ctx.beginPath();
      ctx.arc(impactX, impactY, finalR, 0, Math.PI * 2);
      ctx.fill();
      ctx.stroke();
      
      // Reset shadow
      ctx.shadowBlur = 0;
      
      // Add distance markers on rings (like a ruler)
      if (finalR > 20 && expansion > 0.3) {
        drawDistanceMarkers(finalR, r.km, easedExpansion);
      }
    });
  }
  
  function drawDistanceMarkers(radius, kmValue, expansion) {
    const numMarkers = Math.min(8, Math.floor(radius / 15));
    const markerInterval = (2 * Math.PI) / numMarkers;
    
    ctx.strokeStyle = 'rgba(255,255,255,0.6)';
    ctx.lineWidth = 1;
    ctx.font = '9px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    
    for (let i = 0; i < numMarkers; i++) {
      const angle = i * markerInterval;
      const x1 = impactX + Math.cos(angle) * (radius - 5);
      const y1 = impactY + Math.sin(angle) * (radius - 5);
      const x2 = impactX + Math.cos(angle) * (radius + 5);
      const y2 = impactY + Math.sin(angle) * (radius + 5);
      
      // Draw tick mark
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();
      
      // Add distance label every 4th marker
      if (i % 4 === 0) {
        const labelX = impactX + Math.cos(angle) * (radius + 12);
        const labelY = impactY + Math.sin(angle) * (radius + 12);
        const currentKm = (kmValue * expansion).toFixed(1);
        
        ctx.fillStyle = 'rgba(255,255,255,0.8)';
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 2;
        ctx.strokeText(`${currentKm}km`, labelX, labelY);
        ctx.fillText(`${currentKm}km`, labelX, labelY);
      }
    }
  }

  function drawRingLabels(expansion) {
    ctx.font = '11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
    ctx.textAlign = 'left';
    ctx.textBaseline = 'middle';
    
    rings.forEach((r, index) => {
      const targetR = kmToPx(r.km);
      const currentR = Math.max(0, targetR * expansion);
      if (currentR < 16) return;
      
      // Real-time radius calculation
      const currentKm = (r.km * expansion).toFixed(1);
      const progressPercent = Math.round(expansion * 100);
      
      // place label at different angles for each ring
      const angle = (index * 120 + 45) * Math.PI / 180; // 45°, 165°, 285°
      const dx = currentR * Math.cos(angle);
      const dy = currentR * Math.sin(angle);
      const lx = impactX + dx + 8;
      const ly = impactY - dy;
      
      // Enhanced label with progress indicator
      const labelText = `${r.name}: ${currentKm} km (${progressPercent}%)`;
      
      // Background box for better readability
      const textWidth = ctx.measureText(labelText).width;
      const boxPadding = 4;
      const boxX = lx - 2;
      const boxY = ly - 8;
      const boxW = textWidth + boxPadding * 2;
      const boxH = 16;
      
      // Semi-transparent background
      ctx.fillStyle = 'rgba(0,0,0,0.4)';
      ctx.fillRect(boxX, boxY, boxW, boxH);
      
      // Border
      ctx.strokeStyle = r.colorStroke;
      ctx.lineWidth = 1;
      ctx.strokeRect(boxX, boxY, boxW, boxH);
      
      // Text with outline for legibility
      ctx.fillStyle = '#ffffff';
      ctx.strokeStyle = 'rgba(0,0,0,0.7)';
      ctx.lineWidth = 2;
      ctx.strokeText(labelText, lx, ly);
      ctx.fillText(labelText, lx, ly);
      
      // Add expansion speed indicator
      if (expansion > 0.1 && expansion < 0.9) {
        const speed = Math.abs(Math.sin(expansion * Math.PI * 2)) * 100;
        const speedText = `Speed: ${speed.toFixed(0)}%`;
        ctx.font = '9px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
        ctx.fillStyle = 'rgba(255,255,255,0.7)';
        ctx.strokeStyle = 'rgba(0,0,0,0.5)';
        ctx.lineWidth = 1;
        ctx.strokeText(speedText, lx, ly + 12);
        ctx.fillText(speedText, lx, ly + 12);
        ctx.font = '11px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial'; // reset
      }
    });
  }

  function drawLegend(expansion) {
    const lines = [
      `Energy: ${metrics.energy_megatons_tnt} Mt TNT`,
      `Severity: ${metrics.severity}`,
      `Animation: ${Math.round(expansion * 100)}%`
    ];
    const padX = 10, padY = 8, lineH = 14;
    const boxW = 220, boxH = padY * 2 + lineH * lines.length + 20; // extra space for progress bar
    const x = 8, y = 8;
    
    // background
    ctx.fillStyle = 'rgba(0,0,0,0.4)';
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, boxW, boxH, 8) : ctx.fillRect(x, y, boxW, boxH);
    ctx.fill();
    
    // border
    ctx.strokeStyle = 'rgba(255,255,255,0.2)';
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(x, y, boxW, boxH, 8) : ctx.strokeRect(x, y, boxW, boxH);
    ctx.stroke();
    
    // text
    ctx.fillStyle = '#ffffff';
    ctx.font = '12px system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial';
    lines.forEach((t, i) => ctx.fillText(t, x + padX, y + padY + i * lineH));
    
    // Progress bar
    const progressY = y + padY + lines.length * lineH + 5;
    const progressW = boxW - padX * 2;
    const progressH = 6;
    
    // Background bar
    ctx.fillStyle = 'rgba(255,255,255,0.2)';
    ctx.fillRect(x + padX, progressY, progressW, progressH);
    
    // Progress fill with gradient
    const progressFill = expansion * progressW;
    const gradient = ctx.createLinearGradient(x + padX, progressY, x + padX + progressFill, progressY);
    gradient.addColorStop(0, '#ff6b6b');
    gradient.addColorStop(0.5, '#4ecdc4');
    gradient.addColorStop(1, '#45b7d1');
    
    ctx.fillStyle = gradient;
    ctx.fillRect(x + padX, progressY, progressFill, progressH);
    
    // Progress bar border
    ctx.strokeStyle = 'rgba(255,255,255,0.4)';
    ctx.lineWidth = 1;
    ctx.strokeRect(x + padX, progressY, progressW, progressH);
    
    // Add pulsing effect when near completion
    if (expansion > 0.9) {
      const pulse = Math.sin(expansion * Math.PI * 10) * 0.1 + 0.9;
      ctx.shadowColor = gradient;
      ctx.shadowBlur = 8 * pulse;
      ctx.fillRect(x + padX, progressY, progressFill, progressH);
      ctx.shadowBlur = 0;
    }
  }

  let exploded = false;
  let craterFormed = false;
  let animationComplete = false;
  let restartButton = null;
  
  function resetAnimation() {
    frame = 0;
    exploded = false;
    craterFormed = false;
    animationComplete = false;
    particles.length = 0;
    craterParticles.length = 0;
    if (restartButton) {
      restartButton.remove();
      restartButton = null;
    }
  }
  
  function createRestartButton() {
    if (restartButton) return;
    
    restartButton = document.createElement('button');
    restartButton.textContent = '🔄 Restart Animation';
    restartButton.style.cssText = `
      position: absolute;
      top: 10px;
      right: 10px;
      background: rgba(93,59,141,0.8);
      color: white;
      border: none;
      padding: 8px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      backdrop-filter: blur(10px);
      transition: all 0.3s ease;
    `;
    
    restartButton.addEventListener('mouseenter', () => {
      restartButton.style.background = 'rgba(93,59,141,1)';
      restartButton.style.transform = 'scale(1.05)';
    });
    
    restartButton.addEventListener('mouseleave', () => {
      restartButton.style.background = 'rgba(93,59,141,0.8)';
      restartButton.style.transform = 'scale(1)';
    });
    
    restartButton.addEventListener('click', resetAnimation);
    
    canvas.parentElement.style.position = 'relative';
    canvas.parentElement.appendChild(restartButton);
  }
  
  function tick() {
    clear();
    if (frame < travelTime) {
      const p = frame / travelTime;
      drawMeteor(p);
    } else {
      const ex = Math.min(1, (frame - travelTime) / 90); // quicker expansion
      if (!exploded) { 
        spawnParticles(40); 
        exploded = true; 
      }
      
      // Crater formation timing
      const craterStart = 90;
      const craterFormationTime = 60;
      const craterProgress = Math.max(0, Math.min(1, (frame - craterStart) / craterFormationTime));
      
      if (frame >= craterStart && !craterFormed) {
        spawnCraterParticles();
        craterFormed = true;
      }
      
      drawRings(ex);
      updateParticles();
      drawParticles();
      
             // Animated crater formation
       if (craterProgress > 0) {
         const craterR = Math.max(2, kmToPx(metrics.crater_km || 0) * 0.5);
         const currentCraterR = craterR * craterProgress;
         
         // Draw crater depression with gradient
         const craterGradient = ctx.createRadialGradient(impactX, impactY, 0, impactX, impactY, currentCraterR);
         craterGradient.addColorStop(0, 'rgba(93,59,141,0.6)');
         craterGradient.addColorStop(0.7, 'rgba(93,59,141,0.3)');
         craterGradient.addColorStop(1, 'rgba(93,59,141,0.1)');
         
         ctx.fillStyle = craterGradient;
         ctx.beginPath();
         ctx.arc(impactX, impactY, currentCraterR, 0, Math.PI * 2);
         ctx.fill();
         
         // Draw crater rim with enhanced styling
         ctx.strokeStyle = 'rgba(139,69,19,0.9)';
         ctx.lineWidth = 3;
         ctx.shadowColor = 'rgba(139,69,19,0.5)';
         ctx.shadowBlur = 4;
         ctx.beginPath();
         ctx.arc(impactX, impactY, currentCraterR, 0, Math.PI * 2);
         ctx.stroke();
         
         // Reset shadow
         ctx.shadowBlur = 0;
         
         // Add inner crater detail
         if (craterProgress > 0.5) {
           const innerR = currentCraterR * 0.6;
           ctx.strokeStyle = 'rgba(160,82,45,0.6)';
           ctx.lineWidth = 1;
           ctx.beginPath();
           ctx.arc(impactX, impactY, innerR, 0, Math.PI * 2);
           ctx.stroke();
         }
         
         // Update and draw crater particles
         updateCraterParticles();
         drawCraterParticles();
       }
      
      // Labels & legend
      drawRingLabels(ex);
      drawLegend(ex);
      
      // Check if animation is complete
      if (ex >= 1 && !animationComplete) {
        animationComplete = true;
        createRestartButton();
      }
    }
    frame++;
    requestAnimationFrame(tick);
  }

  // Polyfill for roundRect on older canvases
  if (!CanvasRenderingContext2D.prototype.roundRect) {
    CanvasRenderingContext2D.prototype.roundRect = function(x, y, w, h, r){
      const rr = Math.min(r, w/2, h/2);
      this.beginPath();
      this.moveTo(x + rr, y);
      this.arcTo(x + w, y, x + w, y + h, rr);
      this.arcTo(x + w, y + h, x, y + h, rr);
      this.arcTo(x, y + h, x, y, rr);
      this.arcTo(x, y, x + w, y, rr);
      this.closePath();
    };
  }

  tick();
})(); 
import React, { useEffect, useRef } from 'react';

const SimulationCanvas = ({ gameState }) => {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const roadWidth = 120;
    const laneWidth = roadWidth / 2;

    // --- DRAW BACKGROUND ---
    ctx.fillStyle = '#228B22'; // Grass Green
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // --- DRAW ROADS ---
    ctx.fillStyle = '#34495e'; // Asphalt
    // Vertical Road
    ctx.fillRect(centerX - roadWidth / 2, 0, roadWidth, canvas.height);
    // Horizontal Road
    ctx.fillRect(0, centerY - roadWidth / 2, canvas.width, roadWidth);

    // --- DRAW ROAD MARKINGS ---
    const lanesPer = gameState?.lanes_per_approach ?? 2;
    const subWidth = laneWidth / lanesPer;
    const half = roadWidth / 2;
    const segments = (draw) => { ctx.beginPath(); draw(); ctx.stroke(); };

    // Centre lines separating opposing directions (solid yellow)
    ctx.strokeStyle = '#f1c40f';
    ctx.lineWidth = 3;
    ctx.setLineDash([]);
    segments(() => {
      ctx.moveTo(centerX, 0); ctx.lineTo(centerX, centerY - half);
      ctx.moveTo(centerX, centerY + half); ctx.lineTo(centerX, canvas.height);
      ctx.moveTo(0, centerY); ctx.lineTo(centerX - half, centerY);
      ctx.moveTo(centerX + half, centerY); ctx.lineTo(canvas.width, centerY);
    });

    // Lane dividers within each direction (dashed white)
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 2;
    ctx.setLineDash([14, 14]);
    segments(() => {
      for (let i = 1; i < lanesPer; i++) {
        for (const side of [-1, 1]) {
          const off = side * i * subWidth;
          ctx.moveTo(centerX + off, 0); ctx.lineTo(centerX + off, centerY - half);
          ctx.moveTo(centerX + off, centerY + half); ctx.lineTo(centerX + off, canvas.height);
          ctx.moveTo(0, centerY + off); ctx.lineTo(centerX - half, centerY + off);
          ctx.moveTo(centerX + half, centerY + off); ctx.lineTo(canvas.width, centerY + off);
        }
      }
    });

    ctx.strokeStyle = '#ecf0f1';
    // Stop Lines (Solid)
    ctx.setLineDash([]);
    ctx.lineWidth = 4;

    // North Stop Line
    ctx.beginPath();
    ctx.moveTo(centerX, centerY - roadWidth / 2);
    ctx.lineTo(centerX - roadWidth / 2, centerY - roadWidth / 2);
    ctx.stroke();

    // South Stop Line
    ctx.beginPath();
    ctx.moveTo(centerX, centerY + roadWidth / 2);
    ctx.lineTo(centerX + roadWidth / 2, centerY + roadWidth / 2);
    ctx.stroke();

    // East Stop Line
    ctx.beginPath();
    ctx.moveTo(centerX + roadWidth / 2, centerY);
    ctx.lineTo(centerX + roadWidth / 2, centerY - roadWidth / 2);
    ctx.stroke();

    // West Stop Line
    ctx.beginPath();
    ctx.moveTo(centerX - roadWidth / 2, centerY);
    ctx.lineTo(centerX - roadWidth / 2, centerY + roadWidth / 2);
    ctx.stroke();

    if (!gameState) return;

    // --- DRAW TRAFFIC LIGHTS ---
    const LIGHT_COLORS = { green: '#2ecc71', yellow: '#f1c40f', red: '#e74c3c' };
    const drawLight = (x, y, state) => {
      const color = LIGHT_COLORS[state] ?? state;
      ctx.fillStyle = '#2c3e50';
      ctx.fillRect(x - 10, y - 20, 20, 40);

      ctx.fillStyle = color;
      ctx.shadowBlur = 15;
      ctx.shadowColor = color;
      ctx.beginPath();
      ctx.arc(x, y, 12, 0, 2 * Math.PI);
      ctx.fill();
      ctx.shadowBlur = 0;
    };

    drawLight(centerX - roadWidth / 2 - 20, centerY - roadWidth / 2, gameState.lights.north_south);
    drawLight(centerX + roadWidth / 2 + 20, centerY + roadWidth / 2, gameState.lights.north_south);
    drawLight(centerX + roadWidth / 2, centerY - roadWidth / 2 - 20, gameState.lights.east_west);
    drawLight(centerX - roadWidth / 2, centerY + roadWidth / 2 + 20, gameState.lights.east_west);

    // --- DRAW VEHICLES ---
    const scale = 3.0; // pixels per logical unit
    const WIDTHS = { bike: 6, car: 14, truck: 18 };
    const CAR_COLORS = ['#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#3498db', '#e67e22'];

    // Convert a logical position to screen coordinates of the vehicle's centre.
    // `pos` is the front bumper: 0 is the start of the lane, 100 is the stop line.
    // Sublane 0 is the lane next to the centre line.
    const getCoords = (lane, sublane, pos, lengthPx) => {
      const along = half + (100 - pos) * scale + lengthPx / 2;
      const across = subWidth * (sublane + 0.5);

      if (lane === 0) { // North (moving down)
        return { x: centerX - across, y: centerY - along, angle: 0 };
      } else if (lane === 1) { // South (moving up)
        return { x: centerX + across, y: centerY + along, angle: Math.PI };
      } else if (lane === 2) { // East (moving left)
        return { x: centerX + along, y: centerY - across, angle: Math.PI / 2 };
      } else { // West (moving right)
        return { x: centerX - along, y: centerY + across, angle: -Math.PI / 2 };
      }
    };

    // Drawn in a frame where the vehicle points towards +y (its front is at +length/2).
    const drawVehicle = (v) => {
      const lengthPx = v.length * scale;
      const width = WIDTHS[v.kind] ?? 14;
      const { x, y, angle } = getCoords(v.lane, v.sublane, v.position, lengthPx);
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      if (v.kind === 'truck') {
        ctx.fillStyle = '#bdc3c7'; // trailer
        ctx.fillRect(-width / 2, -lengthPx / 2, width, lengthPx - 9);
        ctx.fillStyle = '#c0392b'; // cab
        ctx.fillRect(-width / 2, lengthPx / 2 - 9, width, 9);
        ctx.fillStyle = '#2c3e50';
        ctx.fillRect(-width / 2 + 2, lengthPx / 2 - 6, width - 4, 3);
      } else if (v.kind === 'bike') {
        ctx.fillStyle = '#ecf0f1';
        ctx.fillRect(-width / 2, -lengthPx / 2, width, lengthPx);
        ctx.fillStyle = '#2c3e50'; // rider
        ctx.beginPath();
        ctx.arc(0, 0, 2.5, 0, 2 * Math.PI);
        ctx.fill();
      } else {
        ctx.fillStyle = CAR_COLORS[v.id % CAR_COLORS.length];
        ctx.fillRect(-width / 2, -lengthPx / 2, width, lengthPx);
        ctx.fillStyle = '#2c3e50'; // windshield
        ctx.fillRect(-width / 2 + 2, lengthPx / 2 - 8, width - 4, 4);
      }
      ctx.restore();
    };

    if (gameState.vehicles) {
      gameState.vehicles.forEach(drawVehicle);
    }

    // --- UPSTREAM BACKLOG (cars queued beyond the visible road) ---
    if (gameState.backlog) {
      const labelPos = [
        [centerX - laneWidth / 2, 14],
        [centerX + laneWidth / 2, canvas.height - 14],
        [canvas.width - 22, centerY - laneWidth / 2],
        [22, centerY + laneWidth / 2],
      ];
      ctx.font = 'bold 14px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      gameState.backlog.forEach((count, lane) => {
        if (count > 0) {
          const [x, y] = labelPos[lane];
          ctx.fillStyle = 'rgba(231, 76, 60, 0.9)';
          ctx.beginPath();
          ctx.arc(x, y, 13, 0, 2 * Math.PI);
          ctx.fill();
          ctx.fillStyle = '#fff';
          ctx.fillText(`+${count}`, x, y);
        }
      });
    }

  }, [gameState]);

  return <canvas ref={canvasRef} width={800} height={600} className="border-4 border-gray-700 rounded-lg shadow-2xl bg-gray-800" />;
};

export default SimulationCanvas;

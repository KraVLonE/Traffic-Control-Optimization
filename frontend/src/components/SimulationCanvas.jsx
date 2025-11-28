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
    const stopLineDist = 100; // Visual distance from center to stop line

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
    ctx.strokeStyle = '#ecf0f1';
    ctx.lineWidth = 2;
    ctx.setLineDash([20, 20]);

    // Vertical Lane Divider
    ctx.beginPath();
    ctx.moveTo(centerX, 0);
    ctx.lineTo(centerX, centerY - roadWidth / 2);
    ctx.moveTo(centerX, centerY + roadWidth / 2);
    ctx.lineTo(centerX, canvas.height);
    ctx.stroke();

    // Horizontal Lane Divider
    ctx.beginPath();
    ctx.moveTo(0, centerY);
    ctx.lineTo(centerX - roadWidth / 2, centerY);
    ctx.moveTo(centerX + roadWidth / 2, centerY);
    ctx.lineTo(canvas.width, centerY);
    ctx.stroke();

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
    const drawLight = (x, y, color) => {
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

    // --- DRAW CARS ---
    const carWidth = 20;
    const carLength = 35;

    // Helper to convert logical position (0-150) to screen coordinates
    // 0 is start of lane (far from intersection), 100 is stop line, 150 is past intersection
    const getCarCoords = (lane, pos) => {
      // Map logical pos 0..100 to screen distance from stop line
      // Stop line is at roadWidth/2 from center
      // Start of lane is e.g. 300px away

      const distFromStopLine = 100 - pos;
      // Scale factor: 3 pixels per logical unit
      const scale = 3.0;

      const offset = (roadWidth / 2) + (distFromStopLine * scale);

      if (lane === 0) { // North(Moving Down)
        return { x: centerX - laneWidth / 2, y: centerY - offset, angle: 0 };
      } else if (lane === 1) { // South(Moving Up)
        return { x: centerX + laneWidth / 2, y: centerY + offset, angle: Math.PI };
      } else if (lane === 2) { // East(Moving Left)
        return { x: centerX + offset, y: centerY - laneWidth / 2, angle: -Math.PI / 2 };
      } else { // West(Moving Right)
        return { x: centerX - offset, y: centerY + laneWidth / 2, angle: Math.PI / 2 };
      }
    };

    const drawCar = (x, y, color, angle) => {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      ctx.fillStyle = color;
      ctx.fillRect(-carWidth / 2, -carLength / 2, carWidth, carLength);
      ctx.fillStyle = '#3498db';
      ctx.fillRect(-carWidth / 2 + 2, -carLength / 2 + 5, carWidth - 4, 8);
      ctx.restore();
    };

    if (gameState.vehicles) {
      gameState.vehicles.forEach(car => {
        const { x, y, angle } = getCarCoords(car.lane, car.position);
        // Color based on speed? Red if stopped, Green if moving?
        // Or just random colors based on ID?
        const colors = ['#e74c3c', '#f1c40f', '#9b59b6', '#1abc9c', '#3498db', '#e67e22'];
        const color = colors[car.id % colors.length];

        drawCar(x, y, color, angle);
      });
    }

  }, [gameState]);

  return <canvas ref={canvasRef} width={800} height={600} className="border-4 border-gray-700 rounded-lg shadow-2xl bg-gray-800" />;
};

export default SimulationCanvas;

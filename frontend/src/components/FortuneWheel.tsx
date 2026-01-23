import React, { useEffect, useRef, useState } from 'react';
import { X, Gift } from 'lucide-react';

interface FortuneWheelProps {
  onClose: () => void;
  onWin: (prize: string) => void;
}

const prizes = [
  { text: 'Знижка 10%', color: '#7C3AED', textColor: '#ffffff' },
  { text: 'Безкоштовна доставка', color: '#DB2777', textColor: '#ffffff' },
  { text: 'Секретний подарунок', color: '#7C3AED', textColor: '#ffffff' },
  { text: 'Знижка 5%', color: '#DB2777', textColor: '#ffffff' },
  { text: 'Спробуй ще раз', color: '#FFFFFF', textColor: '#000000' },
  { text: 'Знижка 15%', color: '#7C3AED', textColor: '#ffffff' },
];

export const FortuneWheel: React.FC<FortuneWheelProps> = ({ onClose, onWin }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isSpinning, setIsSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);

  useEffect(() => {
    drawWheel();
  }, [rotation]); // Redraw whenever rotation changes

  const drawWheel = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = canvas.width;
    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 10; // Leave space for border
    const arcSize = (2 * Math.PI) / prizes.length;

    ctx.clearRect(0, 0, size, size);

    // Draw border
    ctx.beginPath();
    ctx.arc(cx, cy, radius + 5, 0, 2 * Math.PI);
    ctx.fillStyle = '#ddd';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#fff';
    ctx.stroke();

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate(rotation);
    ctx.translate(-cx, -cy);

    prizes.forEach((prize, i) => {
      const angle = i * arcSize;

      // Draw slice
      ctx.beginPath();
      ctx.moveTo(cx, cy);
      ctx.arc(cx, cy, radius, angle, angle + arcSize);
      ctx.lineTo(cx, cy);
      ctx.fillStyle = prize.color;
      ctx.fill();
      ctx.stroke();

      // --- ВИПРАВЛЕНА СЕКЦІЯ МАЛЮВАННЯ ТЕКСТУ ---
      ctx.save();
      // 1. Переміщуємося в центр колеса
      ctx.translate(cx, cy);
      // 2. Повертаємося до середини поточного сектора
      ctx.rotate(angle + arcSize / 2);
      // 3. Зміщуємося по радіусу назовні на 65% від центру.
      // Це розмістить текст візуально посередині "шматка" пирога.
      ctx.translate(radius * 0.65, 0);

      // Налаштування тексту для ідеального центрування
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = prize.textColor;
      // Трохи збільшив шрифт для кращої читабельності
      ctx.font = 'bold 18px Inter, sans-serif';

      // Розрахунок максимальної ширини тексту, щоб він не вилазив за межі сектора.
      // Це приблизна довжина дуги на цій відстані від центру.
      const maxWidth = (radius * 0.65 * arcSize) * 0.9;

      // Малюємо текст у точці (0,0) нової системи координат.
      // Четвертий параметр обмежує максимальну ширину, стискаючи текст за потреби.
      ctx.fillText(prize.text, 0, 0, maxWidth);

      ctx.restore();
      // --- КІНЕЦЬ ВИПРАВЛЕНОЇ СЕКЦІЇ ---
    });

    ctx.restore();

    // Draw center circle
    ctx.beginPath();
    ctx.arc(cx, cy, 25, 0, 2 * Math.PI);
    ctx.fillStyle = 'white';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = '#7C3AED';
    ctx.stroke();

    // Draw star icon
    const iconSize = 24;
    ctx.save();
    ctx.translate(cx - iconSize / 2, cy - iconSize / 2);
    // Simple star drawing using path
    ctx.beginPath();
    ctx.moveTo(12, 2);
    ctx.lineTo(15, 8);
    ctx.lineTo(22, 9);
    ctx.lineTo(17, 14);
    ctx.lineTo(18, 21);
    ctx.lineTo(12, 17);
    ctx.lineTo(6, 21);
    ctx.lineTo(7, 14);
    ctx.lineTo(2, 9);
    ctx.lineTo(9, 8);
    ctx.closePath();
    ctx.fillStyle = '#7C3AED';
    ctx.fill();
    ctx.restore();

    // Draw pointer
    ctx.beginPath();
    ctx.moveTo(size - 10, cy);
    ctx.lineTo(size + 10, cy - 15);
    ctx.lineTo(size + 10, cy + 15);
    ctx.closePath();
    ctx.fillStyle = '#111827';
    ctx.fill();
    ctx.lineWidth = 2;
    ctx.strokeStyle = 'white';
    ctx.stroke();
  };

  const spin = () => {
    if (isSpinning) return;

    setIsSpinning(true);
    const minSpins = 5;
    const extraDegrees = Math.random() * 360;
    const totalRotation = minSpins * 360 + extraDegrees;

    const duration = 4000; // 4 seconds
    const startTime = performance.now();
    const startRotation = rotation;

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic formula
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const currentRotation = startRotation + totalRotation * easeOut;

      setRotation(currentRotation);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsSpinning(false);
        // Calculate winning prize
        const finalRotation = currentRotation % 360;
        // Adjust for pointer position (pointer is at 0 degrees/right side)
        // The standard calculation needs adjustment because canvas 0 angle is exactly where the pointer is.
        // We need to find out which segment is currently crossing 0 degrees.
        // The logic is: (Total Angle - (Rotation % Total Angle)) % Total Angle
        const sectorAngle = 360 / prizes.length;
        // Calculate the index that is currently under the pointer (at angle 0)
        // We normalize the rotation so it's positive, then find how many full rotations passed.
        const normalizedRotation = (360 - (finalRotation % 360)) % 360;
        const prizeIndex = Math.floor(normalizedRotation / sectorAngle);

        onWin(prizes[prizeIndex].text);
      }
    };

    requestAnimationFrame(animate);
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-md relative overflow-hidden">
        <button
          onClick={onClose}
          className="absolute right-4 top-4 text-gray-400 hover:text-gray-600 z-10"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="p-8 text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-purple-100 rounded-full mb-6">
            <Gift className="w-8 h-8 text-purple-600" />
          </div>
          <h2 className="text-2xl font-bold mb-2">Колесо Фортуни</h2>
          <p className="text-gray-600 mb-8">Крути колесо та отримуй гарантовані призи!</p>

          <div className="relative flex justify-center mb-8">
            <canvas
              ref={canvasRef}
              width={320}
              height={320}
              className="max-w-full"
            />
          </div>

          <button
            onClick={spin}
            disabled={isSpinning}
            className="w-full py-3 bg-purple-600 text-white rounded-xl font-semibold text-lg hover:bg-purple-700 transition-colors disabled:opacity-50"
          >
            {isSpinning ? 'Крутимо...' : 'Крутити колесо'}
          </button>
        </div>
      </div>
    </div>
  );
};
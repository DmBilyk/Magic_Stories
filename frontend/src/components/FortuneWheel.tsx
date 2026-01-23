import React, { useEffect, useRef, useState } from 'react';
import { X, Sparkles } from 'lucide-react';

interface WheelSegment {
  text: string;
  color: string;
  textColor: string;
}

// Чорно-біла стилістика під дизайн сайту
const segments: WheelSegment[] = [
  { text: 'Знижка 10%', color: '#000000', textColor: '#ffffff' },
  { text: 'Безкоштовна доставка', color: '#ffffff', textColor: '#000000' },
  { text: 'Секретний подарунок', color: '#000000', textColor: '#ffffff' },
  { text: 'Знижка 5%', color: '#ffffff', textColor: '#000000' },
  { text: 'Знижка 15%', color: '#000000', textColor: '#ffffff' },
  { text: 'Безкоштовна година', color: '#ffffff', textColor: '#000000' },
  { text: 'Знижка 20%', color: '#000000', textColor: '#ffffff' },
  { text: 'Солодкий подарунок', color: '#ffffff', textColor: '#000000' },
];

interface FortuneWheelProps {
  onClose: () => void;
  onWin?: (prize: string) => void;
}

export const FortuneWheel: React.FC<FortuneWheelProps> = ({ onClose, onWin }) => {
  const [isSpinning, setIsSpinning] = useState(false);
  const [rotation, setRotation] = useState(0);
  const [prize, setPrize] = useState<string | null>(null);
  const [hasSpun, setHasSpun] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    drawWheel();
  }, [rotation]);

  const drawWheel = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const size = canvas.width;
    const cx = size / 2;
    const cy = size / 2;
    const radius = size / 2 - 10;

    ctx.clearRect(0, 0, size, size);

    // Тінь для колеса
    ctx.shadowColor = "rgba(0, 0, 0, 0.1)";
    ctx.shadowBlur = 10;
    ctx.shadowOffsetX = 0;
    ctx.shadowOffsetY = 5;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((rotation * Math.PI) / 180);

    const segmentAngle = (2 * Math.PI) / segments.length;

    segments.forEach((segment, i) => {
      const startAngle = i * segmentAngle;
      const endAngle = startAngle + segmentAngle;

      // Малюємо сектор
      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, radius, startAngle, endAngle);
      ctx.closePath();
      ctx.fillStyle = segment.color;
      ctx.fill();
      ctx.stroke();

      // Малюємо текст
      ctx.save();
      ctx.rotate(startAngle + segmentAngle / 2);
      ctx.translate(radius * 0.65, 0); // Посуваємо текст
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = segment.textColor;
      // Шрифт під стиль сайту (Inter, Light)
      ctx.font = '300 14px Inter, sans-serif';

      // Розбиття тексту на рядки, якщо він довгий
      const words = segment.text.split(' ');
      const maxWidth = radius * 0.5; // Обмеження ширини
      let lines: string[] = [];
      let currentLine = '';

      words.forEach(word => {
        const testLine = currentLine ? `${currentLine} ${word}` : word;
        const metrics = ctx.measureText(testLine);
        if (metrics.width > maxWidth && currentLine) {
          lines.push(currentLine);
          currentLine = word;
        } else {
          currentLine = testLine;
        }
      });
      if (currentLine) lines.push(currentLine);

      // Відображення рядків
      lines.forEach((line, index) => {
        const lineHeight = 18;
        const yOffset = (index - (lines.length - 1) / 2) * lineHeight;
        ctx.fillText(line, 0, yOffset);
      });

      ctx.restore();
    });

    ctx.restore();

    // Скидаємо тінь
    ctx.shadowColor = "transparent";

    // Центральне коло
    ctx.beginPath();
    ctx.arc(cx, cy, 30, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = 1;
    ctx.stroke();

    // Декоративна точка в центрі
    ctx.beginPath();
    ctx.arc(cx, cy, 6, 0, 2 * Math.PI);
    ctx.fillStyle = '#000000';
    ctx.fill();
  };

  const spin = () => {
    if (isSpinning || hasSpun) return;

    setIsSpinning(true);
    setPrize(null);

    const winningIndex = Math.floor(Math.random() * segments.length);
    const segmentAngle = 360 / segments.length;

    // Додаємо випадкову кількість повних обертів (5-8)
    const extraSpins = 5 + Math.random() * 3;
    const baseRotation = extraSpins * 360;

    // Розрахунок кута:
    // Canvas 0 градусів - це 3 години (праворуч).
    // Стрілка (в HTML) стоїть зверху (12 годин, -90 градусів).
    // Ми крутимо канвас, тому треба змістити ціль.
    const segmentOffset = winningIndex * segmentAngle;

    // Формула: Базові оберти + (Повне коло - зміщення сегмента) - 90 градусів (поправка на стрілку) + половина сегмента (щоб стрілка була по центру)
    const finalRotation = baseRotation + (360 - segmentOffset) + (segmentAngle / 2) - 90;

    const duration = 4000; // 4 секунди
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Ease out cubic (плавне сповільнення)
      const easeOut = 1 - Math.pow(1 - progress, 4);
      const currentRotation = easeOut * finalRotation;

      setRotation(currentRotation);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsSpinning(false);
        setHasSpun(true);
        const wonPrize = segments[winningIndex].text;
        setPrize(wonPrize);
        if (onWin) onWin(wonPrize);
      }
    };

    requestAnimationFrame(animate);
  };

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-white max-w-2xl w-full max-h-[90vh] overflow-y-auto relative shadow-2xl">
        <button
          onClick={onClose}
          className="absolute right-6 top-6 text-black hover:text-neutral-500 z-10 transition-colors"
        >
          <X className="w-6 h-6" />
        </button>

        <div className="p-8 sm:p-12 text-center">

          <div className="inline-flex items-center gap-2 border border-neutral-200 px-6 py-2 mb-8">
            <Sparkles className="w-4 h-4 text-black" />
            <span className="text-xs font-light tracking-[0.3em] uppercase text-black">
              Спеціальна пропозиція
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-light text-black mb-4 tracking-tight">
            Колесо Фортуни
          </h2>
          <p className="text-neutral-500 font-light mb-10 max-w-md mx-auto">
            Випробуйте удачу та отримайте гарантований подарунок для вашої фотосесії.
          </p>

          <div className="relative inline-block mb-10">
            {/* Стрілка-вказівник (CSS трикутник) */}
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10 drop-shadow-md">
              <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[24px] border-t-black"></div>
            </div>

            <canvas
              ref={canvasRef}
              width={350}
              height={350}
              className="max-w-full h-auto"
            />
          </div>

          {!hasSpun ? (
            <button
              onClick={spin}
              disabled={isSpinning}
              className="px-12 py-4 bg-black text-white font-light tracking-wider text-sm uppercase hover:bg-neutral-800 transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {isSpinning ? 'Крутимо...' : 'Крутити колесо'}
            </button>
          ) : (
            <div className="animate-in fade-in slide-in-from-bottom-4 duration-700">
              <div className="border-t border-neutral-100 pt-8">
                <div className="mb-6">
                  <span className="text-xs font-light tracking-[0.2em] uppercase text-neutral-400 block mb-2">
                    Ваш виграш
                  </span>
                  <div className="text-2xl sm:text-3xl font-light text-black tracking-tight border border-black p-4 inline-block min-w-[200px]">
                    {prize}
                  </div>
                </div>

                <div className="bg-neutral-50 p-6 max-w-md mx-auto mb-8 border border-neutral-100">
                  <p className="text-sm text-neutral-600 font-light leading-relaxed">
                    <strong className="text-black font-medium block mb-1 uppercase tracking-wide text-xs">Як отримати:</strong>
                    Зробіть скріншот цього екрану та покажіть його адміністратору при бронюванні або оплаті.
                    <br/><span className="text-xs text-neutral-400 mt-2 block">Пропозиція діє протягом 30 днів.</span>
                  </p>
                </div>

                <button
                  onClick={onClose}
                  className="px-10 py-3 border border-black text-black font-light tracking-wider hover:bg-black hover:text-white transition-colors text-sm uppercase"
                >
                  Закрити
                </button>
              </div>
            </div>
          )}

          {!hasSpun && !isSpinning && (
            <p className="text-[10px] text-neutral-300 font-light mt-6 tracking-widest uppercase">
              Лише одна спроба
            </p>
          )}
        </div>
      </div>
    </div>
  );
};
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

const WHEEL_SIZE = 360;
const POINTER_ANGLE = 270;

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
  const segmentAngleDegrees = 360 / segments.length;
  const segmentAngleRadians = (2 * Math.PI) / segments.length;

  const getSegmentIndexFromRotation = (value: number) => {
    const normalized = ((value % 360) + 360) % 360;
    const pointerOffset = (POINTER_ANGLE - normalized + 360) % 360;
    return Math.floor(pointerOffset / segmentAngleDegrees) % segments.length;
  };

  useEffect(() => {
    drawWheel();
  }, [rotation]);

  const drawWheel = () => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const dpr = typeof window !== 'undefined' ? window.devicePixelRatio || 1 : 1;
    if (canvas.width !== WHEEL_SIZE * dpr || canvas.height !== WHEEL_SIZE * dpr) {
      canvas.width = WHEEL_SIZE * dpr;
      canvas.height = WHEEL_SIZE * dpr;
      canvas.style.width = `${WHEEL_SIZE}px`;
      canvas.style.height = `${WHEEL_SIZE}px`;
    }

    ctx.save();
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.scale(dpr, dpr);

    const cx = WHEEL_SIZE / 2;
    const cy = WHEEL_SIZE / 2;
    const radius = WHEEL_SIZE / 2 - 18;
    const highlightedIndex = getSegmentIndexFromRotation(rotation);

    ctx.shadowColor = 'rgba(0, 0, 0, 0.18)';
    ctx.shadowBlur = 25;
    ctx.shadowOffsetY = 12;

    ctx.save();
    ctx.translate(cx, cy);
    ctx.rotate((rotation * Math.PI) / 180);

    segments.forEach((segment, i) => {
      const startAngle = i * segmentAngleRadians;
      const endAngle = startAngle + segmentAngleRadians;
      const isHighlighted = highlightedIndex === i;
      const baseFill = segment.color;
      const fillStyle = isHighlighted
        ? baseFill === '#000000'
          ? '#111111'
          : '#f8f8f8'
        : baseFill;

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, radius, startAngle, endAngle);
      ctx.closePath();
      ctx.fillStyle = fillStyle;
      ctx.fill();

      const outlineGradient = ctx.createLinearGradient(-radius, -radius, radius, radius);
      outlineGradient.addColorStop(0, isHighlighted ? '#bfbfbf' : '#dadada');
      outlineGradient.addColorStop(1, isHighlighted ? '#7a7a7a' : '#b0b0b0');
      ctx.strokeStyle = outlineGradient;
      ctx.lineWidth = isHighlighted ? 3 : 1.2;
      ctx.stroke();

      ctx.save();
      ctx.rotate(startAngle + segmentAngleRadians / 2);
      ctx.translate(radius * 0.65, 0);
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillStyle = segment.textColor;
      ctx.font = `${isHighlighted ? 400 : 300} 14px "Inter", sans-serif`;

      const words = segment.text.split(' ');
      const maxWidth = radius * 0.5;
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

      lines.forEach((line, index) => {
        const lineHeight = 18;
        const yOffset = (index - (lines.length - 1) / 2) * lineHeight;
        ctx.fillText(line, 0, yOffset);
      });

      ctx.restore();
    });

    ctx.restore();

    ctx.shadowColor = 'transparent';

    ctx.beginPath();
    ctx.arc(cx, cy, radius + 10, 0, 2 * Math.PI);
    ctx.lineWidth = 4;
    ctx.strokeStyle = '#111111';
    ctx.stroke();

    const centerGradient = ctx.createRadialGradient(cx, cy, 4, cx, cy, 32);
    centerGradient.addColorStop(0, '#ffffff');
    centerGradient.addColorStop(1, '#cfcfcf');

    ctx.beginPath();
    ctx.arc(cx, cy, 32, 0, 2 * Math.PI);
    ctx.fillStyle = centerGradient;
    ctx.fill();
    ctx.lineWidth = 1.6;
    ctx.strokeStyle = '#111111';
    ctx.stroke();

    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#000000';
    ctx.fill();

    ctx.restore();
  };

  const spin = () => {
    if (isSpinning || hasSpun) return;

    setIsSpinning(true);
    setPrize(null);

    const winningIndex = Math.floor(Math.random() * segments.length);
    const segmentCenter = winningIndex * segmentAngleDegrees + segmentAngleDegrees / 2;
    const alignmentRotation = (POINTER_ANGLE - segmentCenter + 360) % 360;
    const extraSpins = Math.floor(5 + Math.random() * 4);
    const finalRotation = extraSpins * 360 + alignmentRotation;

    const duration = 4200;
    const startTime = performance.now();

    const animate = (currentTime: number) => {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);
      const easeOut = 1 - Math.pow(1 - progress, 4);
      const currentRotation = easeOut * finalRotation;

      setRotation(currentRotation);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsSpinning(false);
        setHasSpun(true);
        const resolvedIndex = getSegmentIndexFromRotation(currentRotation);
        const wonPrize = segments[resolvedIndex].text;
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
            <div className="absolute -top-4 left-1/2 -translate-x-1/2 z-10 drop-shadow-md">
              <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[24px] border-t-black"></div>
            </div>

            <canvas
              ref={canvasRef}
              width={WHEEL_SIZE}
              height={WHEEL_SIZE}
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

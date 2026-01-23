import { useState, useRef, useEffect } from 'react';
import { X, Sparkles } from 'lucide-react';

interface WheelSegment {
  text: string;
  color: string;
}

const segments: WheelSegment[] = [
  { text: 'Безкоштовна година оренди', color: '#1a1a1a' },
  { text: '50% знижка на реквізит', color: '#404040' },
  { text: 'Додаткова година зі знижкою', color: '#1a1a1a' },
  { text: 'Безкоштовний фон для зйомки', color: '#404040' },
  { text: '30% знижка на наступне бронювання', color: '#1a1a1a' },
  { text: 'Подарункова сертифікат 500₴', color: '#404040' },
  { text: 'Безкоштовне продовження 15 хв', color: '#1a1a1a' },
  { text: '20% знижка на послуги студії', color: '#404040' },
];

interface FortuneWheelProps {
  onClose?: () => void;
}

export default function FortuneWheel({ onClose }: FortuneWheelProps) {
  const [isOpen, setIsOpen] = useState(true);

  const handleClose = () => {
    setIsOpen(false);
    onClose?.();
  };
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

    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = canvas.width / 2 - 10;

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.save();
    ctx.translate(centerX, centerY);
    ctx.rotate((rotation * Math.PI) / 180);

    const segmentAngle = (2 * Math.PI) / segments.length;

    segments.forEach((segment, i) => {
      const startAngle = i * segmentAngle;
      const endAngle = startAngle + segmentAngle;

      ctx.beginPath();
      ctx.moveTo(0, 0);
      ctx.arc(0, 0, radius, startAngle, endAngle);
      ctx.closePath();
      ctx.fillStyle = segment.color;
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      ctx.save();
      ctx.rotate(startAngle + segmentAngle / 2);
      ctx.textAlign = 'center';
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 13px -apple-system, BlinkMacSystemFont, sans-serif';

      const words = segment.text.split(' ');
      const maxWidth = radius * 0.7;
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

      const lineHeight = 16;
      const totalHeight = lines.length * lineHeight;
      const startY = radius * 0.6 - totalHeight / 2;

      lines.forEach((line, index) => {
        ctx.fillText(line, radius * 0.6, startY + index * lineHeight);
      });

      ctx.restore();
    });

    ctx.restore();

    // Center circle
    ctx.beginPath();
    ctx.arc(centerX, centerY, 30, 0, 2 * Math.PI);
    ctx.fillStyle = '#ffffff';
    ctx.fill();
    ctx.strokeStyle = '#1a1a1a';
    ctx.lineWidth = 3;
    ctx.stroke();

    // Center dot
    ctx.beginPath();
    ctx.arc(centerX, centerY, 8, 0, 2 * Math.PI);
    ctx.fillStyle = '#1a1a1a';
    ctx.fill();
  };

  const spinWheel = () => {
    if (isSpinning || hasSpun) return;

    setIsSpinning(true);
    setPrize(null);

    const winningIndex = Math.floor(Math.random() * segments.length);
    const segmentAngle = 360 / segments.length;
    const extraSpins = 5 + Math.random() * 3;
    const baseRotation = extraSpins * 360;
    const segmentOffset = winningIndex * segmentAngle;
    const finalRotation = baseRotation + (360 - segmentOffset) + segmentAngle / 2 - 90;

    let startTime: number | null = null;
    const duration = 4000;

    const animate = (currentTime: number) => {
      if (!startTime) startTime = currentTime;
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      const easeOut = 1 - Math.pow(1 - progress, 4);
      const currentRotation = easeOut * finalRotation;

      setRotation(currentRotation);

      if (progress < 1) {
        requestAnimationFrame(animate);
      } else {
        setIsSpinning(false);
        setPrize(segments[winningIndex].text);
        setHasSpun(true);
      }
    };

    requestAnimationFrame(animate);
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
      <div className="relative bg-white max-w-2xl w-full max-h-[95vh] overflow-y-auto">
        <button
          onClick={handleClose}
          className="absolute top-6 right-6 z-10 w-10 h-10 border border-neutral-200 flex items-center justify-center hover:border-black transition-colors bg-white"
        >
          <X className="w-5 h-5" />
        </button>

        <div className="p-8 sm:p-12 text-center">
          <div className="inline-flex items-center gap-2 border border-neutral-200 px-6 py-2 mb-8">
            <Sparkles className="w-4 h-4" />
            <span className="text-xs font-light tracking-[0.3em] uppercase">
              СПЕЦІАЛЬНА ПРОПОЗИЦІЯ
            </span>
          </div>

          <h2 className="text-3xl sm:text-4xl font-light text-black mb-4 tracking-tight">
            Крутіть колесо фортуни!
          </h2>
          <p className="text-neutral-500 font-light mb-12 max-w-md mx-auto">
            Отримайте шанс виграти спеціальну знижку або безкоштовну послугу для вашої зйомки
          </p>

          <div className="relative inline-block mb-8">
            {/* Arrow pointer */}
            <div className="absolute -top-2 left-1/2 -translate-x-1/2 z-10">
              <div className="w-0 h-0 border-l-[15px] border-l-transparent border-r-[15px] border-r-transparent border-t-[25px] border-t-black drop-shadow-lg"></div>
            </div>

            <canvas
              ref={canvasRef}
              width={400}
              height={400}
              className="max-w-full h-auto drop-shadow-2xl"
            />
          </div>

          {!hasSpun ? (
            <button
              onClick={spinWheel}
              disabled={isSpinning}
              className={`px-12 py-4 bg-black text-white font-light tracking-wider text-sm uppercase transition-all ${
                isSpinning
                  ? 'opacity-50 cursor-not-allowed'
                  : 'hover:bg-neutral-800'
              }`}
            >
              {isSpinning ? 'КРУТИТЬСЯ...' : 'КРУТИТИ КОЛЕСО'}
            </button>
          ) : (
            <div className="border-t border-neutral-200 pt-8 mt-8">
              <div className="inline-block border border-black px-6 py-3 mb-6">
                <span className="text-xs font-light tracking-[0.2em] uppercase text-black">
                  🎉 Вітаємо!
                </span>
              </div>

              <h3 className="text-2xl font-light text-black mb-4">
                Ви виграли:
              </h3>
              <p className="text-xl font-light text-black mb-8 px-4">
                {prize}
              </p>

              <div className="bg-neutral-50 border border-neutral-200 p-6 mb-6">
                <p className="text-sm text-neutral-600 font-light leading-relaxed">
                  <strong className="text-black">Як скористатися:</strong><br />
                  Зробіть скріншот цього повідомлення та покажіть його адміністратору студії при бронюванні. Пропозиція діє протягом 30 днів.
                </p>
              </div>

              <button
                onClick={handleClose}
                className="px-10 py-3 border border-black text-black font-light tracking-wider hover:bg-black hover:text-white transition-colors text-sm uppercase"
              >
                ЗБЕРЕГТИ І ЗАКРИТИ
              </button>
            </div>
          )}

          {!hasSpun && (
            <p className="text-xs text-neutral-400 font-light mt-8 tracking-wider uppercase">
              Ви можете крутити колесо лише один раз
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
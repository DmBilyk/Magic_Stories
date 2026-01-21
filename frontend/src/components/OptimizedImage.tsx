import { useState, useEffect, useRef } from 'react';

interface OptimizedImageProps {
  src: string;        // High-res or Thumbnail URL (якщо це основне фото)
  alt: string;
  className?: string;
  priority?: boolean; // Якщо true - вантажить одразу, false - lazy load
  aspectRatio?: string; // Tailwind class, e.g., 'aspect-[3/4]'
}

export const OptimizedImage = ({
  src,
  alt,
  className = '',
  priority = false,
  aspectRatio
}: OptimizedImageProps) => {
  const [loaded, setLoaded] = useState(false);
  const [isInView, setIsInView] = useState(priority);
  const imgRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (priority || !imgRef.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setIsInView(true);
            observer.disconnect();
          }
        });
      },
      { rootMargin: '100px' } // Почати вантажити за 100px до появи
    );

    observer.observe(imgRef.current);
    return () => observer.disconnect();
  }, [priority]);

  return (
    <div ref={imgRef} className={`relative overflow-hidden bg-neutral-100 ${aspectRatio || ''} ${className}`}>
      {/* Placeholder / Loading State */}
      {!loaded && (
        <div className="absolute inset-0 bg-neutral-200 animate-pulse" />
      )}

      {isInView && (
        <img
          src={src}
          alt={alt}
          loading={priority ? 'eager' : 'lazy'}
          decoding="async"
          onLoad={() => setLoaded(true)}
          className={`w-full h-full object-cover transition-opacity duration-500 ${
            loaded ? 'opacity-100' : 'opacity-0'
          }`}
        />
      )}
    </div>
  );
};
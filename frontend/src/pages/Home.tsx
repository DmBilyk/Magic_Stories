import { useState, useEffect } from 'react';
import { MapPin, Users, ChevronRight, Check, ArrowRight } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { locationService } from '../services/api';
import { useBooking } from '../context/BookingContext';
import { ErrorMessage } from '../components/ErrorMessage';
import { Header } from '../components/Header';
import type { Location } from '../types';
import { formatCurrency } from '../utils/dateTime';
import { HomeSkeleton } from '../components/Skeleton';

export const Home = () => {
  // Змінюємо логіку: зберігаємо масив локацій, а не одну
  const [locations, setLocations] = useState<Location[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const { setSelectedLocation } = useBooking();

  useEffect(() => {
    loadStudioData();
  }, []);

  const loadStudioData = async () => {
    try {
      setLoading(true);
      const data = await locationService.getAll();
      // Сортуємо так, щоб основна студія була першою, а вулична - другою
      // (Можна сортувати за order, якщо він є, або просто за створенням)
      const activeLocations = data.filter((loc) => loc.isActive);

      setLocations(activeLocations);
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load studio data');
    } finally {
      setLoading(false);
    }
  };

  // Ця функція тепер приймає конкретну локацію
  const handleBookLocation = (location: Location) => {
    setSelectedLocation(location);
    navigate('/booking');
  };

  if (loading) return <HomeSkeleton />;
  if (error || locations.length === 0) return <div className="min-h-screen flex items-center justify-center bg-white p-4"><ErrorMessage message={error || 'Локації наразі недоступні'} /></div>;

  // Основна локація (для Hero банера) - це завжди перша у списку
  const mainLocation = locations[0];

  // Галерея для основної локації
  const gallery = [
    ...(mainLocation.imageUrl ? [mainLocation.imageUrl] : []),
    ...(mainLocation.galleryImages?.map(img => img.imageUrl) || [])
  ];

  return (
    <div className="min-h-screen bg-white">
      <Header />

      {/* Hero Section - Показуємо ТІЛЬКИ основну студію для вау-ефекту */}
      <div className="relative h-screen w-full">
        <div className="absolute inset-0">
          {mainLocation.imageUrl ? (
            <img
              src={mainLocation.imageUrl}
              alt={mainLocation.name}
              className="w-full h-full object-cover"
            />
          ) : (
            <div className="w-full h-full bg-neutral-50 flex items-center justify-center">
              <span className="text-neutral-400 font-light">No Image Available</span>
            </div>
          )}
          <div className="absolute inset-0 bg-black/40" />
        </div>

        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center px-6 max-w-4xl">
            <div className="inline-block border border-white/30 px-6 py-2 mb-12">
              <span className="text-white font-light tracking-[0.3em] uppercase text-xs">
                Преміум простір
              </span>
            </div>

            <h1 className="text-5xl sm:text-6xl md:text-7xl font-light text-white mb-8 tracking-tight">
              {mainLocation.name}
            </h1>
            <p className="text-lg sm:text-xl text-white/90 mb-16 font-light leading-relaxed">
              {mainLocation.description}
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <button
                // Тут ми бронюємо саме основну локацію
                onClick={() => handleBookLocation(mainLocation)}
                className="w-full sm:w-auto bg-white text-black px-12 py-4 font-light tracking-wider hover:bg-neutral-100 transition-colors text-sm uppercase flex items-center justify-center group"
              >
                <span>Забронювати цю залу</span>
                <ChevronRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* About Section (Загальна або про основну студію) */}
      <div id="about" className="max-w-7xl mx-auto px-6 py-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-start">
          <div>
            <div className="inline-block border-b border-neutral-200 pb-2 mb-8">
              <h2 className="text-xs font-light tracking-[0.3em] uppercase text-neutral-400">
                Про простір
              </h2>
            </div>
            <h3 className="text-4xl sm:text-5xl font-light text-black mb-8 leading-tight tracking-tight">
              Місце, де народжуються ідеї
            </h3>
            <p className="text-lg text-neutral-500 leading-relaxed mb-12 font-light">
              {mainLocation.description}
            </p>
          </div>

          {/* Amenities */}
          <div id="amenities">
            <div className="inline-block border-b border-neutral-200 pb-2 mb-12">
              <h2 className="text-xs font-light tracking-[0.3em] uppercase text-neutral-400">
                Можливості
              </h2>
            </div>
            <div className="space-y-6">
              {mainLocation.amenities && mainLocation.amenities.map((amenity, index) => (
                <div
                  key={index}
                  className="flex items-center pb-6 border-b border-neutral-100 last:border-0 group"
                >
                  <div className="w-10 h-10 border border-neutral-200 flex items-center justify-center mr-6 group-hover:border-black transition-colors flex-shrink-0">
                    <Check className="w-5 h-5 text-black" />
                  </div>
                  <span className="text-black font-light text-lg">{amenity}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* === НОВА СЕКЦІЯ: ОБЕРІТЬ ЛОКАЦІЮ === */}
      {/* Тут ми показуємо картки ВСІХ локацій (Студія + Вулиця) */}
      <div id="locations" className="bg-neutral-50 py-32">
        <div className="max-w-7xl mx-auto px-6">
          <div className="text-center mb-20">
            <h2 className="text-4xl font-light text-black mb-6 tracking-tight">Наші Локації</h2>
            <p className="text-neutral-500 font-light">Оберіть простір, який найкраще підходить для вашої ідеї</p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
            {locations.map((location) => (
              <div key={location.id} className="group bg-white border border-neutral-200 hover:border-black transition-colors duration-300">
                {/* Image */}
                <div className="aspect-[16/10] overflow-hidden relative">
                  {location.imageUrl ? (
                    <img
                      src={location.imageUrl}
                      alt={location.name}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                  ) : (
                    <div className="w-full h-full bg-neutral-100 flex items-center justify-center">
                      <MapPin className="w-12 h-12 text-neutral-300" />
                    </div>
                  )}
                  {/* Badge: Price */}
                  <div className="absolute top-6 right-6 bg-white px-4 py-2">
                    <span className="text-sm font-light text-black tracking-wider">
                      {formatCurrency(location.hourlyRate)} / год
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="p-10">
                  <h3 className="text-2xl font-light text-black mb-4">{location.name}</h3>
                  <p className="text-neutral-500 font-light mb-8 line-clamp-2 h-12">
                    {location.description}
                  </p>

                  <div className="flex items-center justify-between border-t border-neutral-100 pt-8">
                     <div className="flex items-center text-neutral-400">
                        <Users className="w-4 h-4 mr-2" />
                        <span className="text-xs uppercase tracking-wider">до {location.capacity} осіб</span>
                     </div>

                     <button
                        onClick={() => handleBookLocation(location)}
                        className="flex items-center text-black font-light text-sm uppercase tracking-wider hover:opacity-70 transition-opacity"
                     >
                        Забронювати
                        <ArrowRight className="ml-2 w-4 h-4" />
                     </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Gallery Section */}
      {gallery.length > 1 && (
        <div id="gallery" className="bg-white py-32">
          <div className="max-w-7xl mx-auto px-6">
            <div className="mb-16">
              <div className="inline-block border-b border-neutral-200 pb-2 mb-4">
                <h2 className="text-xs font-light tracking-[0.3em] uppercase text-neutral-400">
                  Галерея
                </h2>
              </div>
              <h3 className="text-3xl font-light text-black tracking-tight">Інтер'єр основної зали</h3>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2">
              {gallery.map((imgUrl, index) => (
                <div
                  key={index}
                  className={`relative overflow-hidden group cursor-pointer border border-neutral-200 hover:border-black transition-colors ${
                    index === 0 ? 'sm:col-span-2 sm:row-span-2' : ''
                  }`}
                >
                  <div className={`relative ${index === 0 ? 'aspect-[4/3]' : 'aspect-square'}`}>
                    <img
                      src={imgUrl}
                      alt={`Studio view ${index + 1}`}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* CTA Section */}
      <div className="py-32 px-6 bg-black text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-4xl sm:text-5xl font-light text-white mb-6 tracking-tight">
            Готові до зйомки?
          </h2>
          <p className="text-neutral-400 text-lg mb-12 font-light">
            Оберіть локацію, яка надихає вас найбільше.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
             {locations.map(loc => (
                <button
                    key={loc.id}
                    onClick={() => handleBookLocation(loc)}
                    className="px-8 py-4 bg-white text-black font-light tracking-wider hover:bg-neutral-200 transition-colors text-sm uppercase"
                >
                    Бронювати: {loc.name}
                </button>
             ))}
          </div>
        </div>
      </div>
    </div>
  );
};
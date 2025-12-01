import { useState, useEffect } from 'react';
import { MapPin, Users, ChevronRight, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { locationService } from '../services/api';
import { useBooking } from '../context/BookingContext';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { Header } from '../components/Header';
import type { Location } from '../types';
import { formatCurrency } from '../utils/dateTime';

export const Home = () => {
  const [mainLocation, setMainLocation] = useState<Location | null>(null);
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
      const activeLocations = data.filter((loc) => loc.isActive);
      if (activeLocations.length > 0) {
        setMainLocation(activeLocations[0]);
      }
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load studio data');
    } finally {
      setLoading(false);
    }
  };

  const handleBookNow = () => {
    if (mainLocation) {
      setSelectedLocation(mainLocation);
      navigate('/booking');
    }
  };

  if (loading) return <div className="min-h-screen flex items-center justify-center bg-white"><LoadingSpinner size="lg" /></div>;
  if (error || !mainLocation) return <div className="min-h-screen flex items-center justify-center bg-white p-4"><ErrorMessage message={error || 'Студія наразі недоступна'} /></div>;

  const gallery = [
    ...(mainLocation.imageUrl ? [mainLocation.imageUrl] : []),
    ...(mainLocation.galleryImages?.map(img => img.imageUrl) || [])
  ];

  return (
    <div className="min-h-screen bg-white">
      <Header />

      {/* Hero Section */}
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
                onClick={handleBookNow}
                className="w-full sm:w-auto bg-white text-black px-12 py-4 font-light tracking-wider hover:bg-neutral-100 transition-colors text-sm uppercase flex items-center justify-center group"
              >
                <span>Забронювати</span>
                <ChevronRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </button>

              <div className="flex items-center gap-8 px-8 py-4 border border-white/30 text-white">
                <div className="flex items-center">
                  <Users className="w-4 h-4 mr-2" />
                  <span className="font-light text-sm">до {mainLocation.capacity} осіб</span>
                </div>
                <div className="w-px h-4 bg-white/30"></div>
                <div className="font-light text-sm">
                  {formatCurrency(mainLocation.hourlyRate)} / год
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* About Section */}
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

            {mainLocation.address && (
              <div className="flex items-start border-t border-neutral-200 pt-6">
                <MapPin className="w-5 h-5 text-black mr-4 mt-1 flex-shrink-0" />
                <span className="text-black font-light">{mainLocation.address}</span>
              </div>
            )}
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

      {/* Gallery Section */}
      {gallery.length > 1 && (
        <div id="gallery" className="bg-neutral-50 py-32">
          <div className="max-w-7xl mx-auto px-6">
            <div className="mb-16">
              <div className="inline-block border-b border-neutral-200 pb-2 mb-4">
                <h2 className="text-xs font-light tracking-[0.3em] uppercase text-neutral-400">
                  Галерея
                </h2>
              </div>
              <h3 className="text-3xl font-light text-black tracking-tight">Інтер'єр та деталі</h3>
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
      <div className="py-32 px-6 bg-white text-center">
        <div className="max-w-3xl mx-auto">
          <h2 className="text-4xl sm:text-5xl font-light text-black mb-6 tracking-tight">
            Готові до зйомки?
          </h2>
          <p className="text-neutral-500 text-lg mb-12 font-light">
            Оберіть дату, час та додаткові послуги в кілька кліків.
          </p>
          <button
            onClick={handleBookNow}
            className="inline-flex items-center px-12 py-4 bg-black text-white font-light tracking-wider hover:bg-neutral-800 transition-colors text-sm uppercase group"
          >
            <span>Забронювати зараз</span>
            <ChevronRight className="ml-2 w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </button>
        </div>
      </div>
    </div>
  );
};
import { useState, useEffect, useCallback, useMemo, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Clock, User, ArrowLeft, Plus,
  MapPin, Calendar, ChevronRight
} from 'lucide-react';
import { useBooking } from '../context/BookingContext';
import { bookingService, serviceAPI, availabilityService } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { BookingFormSkeleton } from '../components/Skeleton';
import { ErrorMessage } from '../components/ErrorMessage';
import { DatePicker } from '../components/DatePicker';
import type { AdditionalService, BookingSettings, TimeSlot } from '../types';
import {
  getTodayDate,
  getMaxBookingDate,
  formatTime,
  isTimeSlotInPast,
  formatCurrency,
} from '../utils/dateTime';
import {
  validatePhoneNumber,
  validateEmail,
  validateName,
  validateNotes,
  normalizePhoneNumber
} from '../utils/validation';

const LOCATION_1_UUID = '136eade1-873d-48cb-a604-2f5e54706f02';

// 🚀 Debounce hook
function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}

// 🚀 Простий кеш для API
const apiCache = new Map<string, { data: any; timestamp: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 хвилин

function getCached<T>(key: string): T | null {
  const cached = apiCache.get(key);
  if (!cached) return null;

  if (Date.now() - cached.timestamp > CACHE_TTL) {
    apiCache.delete(key);
    return null;
  }

  return cached.data as T;
}

function setCache(key: string, data: any): void {
  apiCache.set(key, { data, timestamp: Date.now() });
}

export const BookingForm = () => {
  const navigate = useNavigate();
  const {
    selectedLocation,
    bookingDate,
    setBookingDate,
    bookingTime,
    setBookingTime,
    durationHours,
    setDurationHours,
    selectedServices,
    setSelectedServices,
    contactInfo,
    setContactInfo,
  } = useBooking();

  const [settings, setSettings] = useState<BookingSettings | null>(null);
  const [services, setServices] = useState<AdditionalService[]>([]);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);

  // 🚀 Об'єднуємо form states в один об'єкт для менших ре-рендерів
  const [formData, setFormData] = useState({
    firstName: contactInfo.firstName || '',
    lastName: contactInfo.lastName || '',
    phone: contactInfo.phone || '',
    email: contactInfo.email || '',
    notes: contactInfo.notes || '',
  });

  const [loading, setLoading] = useState(true);
  const [checkingSlots, setCheckingSlots] = useState(false);
  const [error, setError] = useState('');
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  // 🚀 Debounce для перевірки слотів
  const debouncedDate = useDebounce(bookingDate, 300);
  const debouncedDuration = useDebounce(durationHours, 300);

  // 🚀 Ref для відстеження попереднього запиту
  const previousCheckRef = useRef<string>('');

  const getMinDuration = useCallback((): number => {
    if (!selectedLocation) return 0.5;
    return selectedLocation.id === LOCATION_1_UUID ? 1 : 0.5;
  }, [selectedLocation]);

  useEffect(() => {
    if (!selectedLocation) {
      navigate('/');
      return;
    }
    loadInitialData();
  }, [selectedLocation, navigate]);

  // 🚀 Оптимізована перевірка availability з debounce і кешем
  useEffect(() => {
    if (debouncedDate && selectedLocation && settings && debouncedDuration > 0) {
      checkAvailability();
    }
  }, [debouncedDate, debouncedDuration, selectedLocation, settings]);

  useEffect(() => {
    if (selectedLocation) {
      const minDur = getMinDuration();
      if (durationHours < minDur) {
        setDurationHours(minDur);
      }
    }
  }, [selectedLocation, getMinDuration]);

  // 🚀 Кешування settings і services
  const loadInitialData = async () => {
    try {
      setLoading(true);

      // Перевіряємо кеш
      const cachedSettings = getCached<BookingSettings>('booking_settings');
      const cachedServices = getCached<AdditionalService[]>('additional_services');

      if (cachedSettings && cachedServices) {
        setSettings(cachedSettings);
        setServices(cachedServices.filter((s) => s.isActive));

        const minDur = getMinDuration();
        if (!durationHours || durationHours < minDur) {
          setDurationHours(minDur);
        }

        setLoading(false);
        return;
      }

      // Якщо немає в кеші - робимо запит
      const [settingsData, servicesData] = await Promise.all([
        bookingService.getSettings(),
        serviceAPI.getAll(),
      ]);

      // Зберігаємо в кеш
      setCache('booking_settings', settingsData);
      setCache('additional_services', servicesData);

      setSettings(settingsData);

      const minDur = getMinDuration();
      if (!durationHours || durationHours < minDur) {
        setDurationHours(minDur);
      }

      setServices(servicesData.filter((s) => s.isActive));
      setError('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load booking data');
      setDurationHours(getMinDuration());
    } finally {
      setLoading(false);
    }
  };

  // 🚀 Оптимізована перевірка з кешем і dedupe
  const checkAvailability = async () => {
    if (!selectedLocation || !debouncedDate || !debouncedDuration) return;

    // Генеруємо ключ для запиту
    const checkKey = `${debouncedDate}-${debouncedDuration}-${selectedLocation.id}`;

    // Якщо це той самий запит - пропускаємо
    if (previousCheckRef.current === checkKey) {
      return;
    }

    previousCheckRef.current = checkKey;

    // Перевіряємо кеш
    const cacheKey = `availability_${checkKey}`;
    const cached = getCached<TimeSlot[]>(cacheKey);

    if (cached) {
      setAvailableSlots(cached);
      if (bookingTime && !cached.some((s) => s.startTime === bookingTime && s.available)) {
        setBookingTime('');
      }
      return;
    }

    try {
      setCheckingSlots(true);
      const response = await availabilityService.checkAvailability(
        debouncedDate,
        debouncedDuration,
        selectedLocation.id
      );

      const formattedSlots = response.slots.map((slot) => ({
        startTime: slot.start_time,
        endTime: slot.end_time,
        available: slot.available,
      }));

      // Зберігаємо в кеш
      setCache(cacheKey, formattedSlots);

      setAvailableSlots(formattedSlots);
      setError('');

      if (bookingTime && !formattedSlots.some((s) => s.startTime === bookingTime && s.available)) {
        setBookingTime('');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to check availability');
      setAvailableSlots([]);
    } finally {
      setCheckingSlots(false);
    }
  };

  // 🚀 Оптимізовані обробники форми
  const updateFormField = useCallback((field: keyof typeof formData, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    setValidationErrors(prev => ({ ...prev, [field]: '' }));
  }, []);

  const handlePhoneChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    if (value.length < 4) {
      updateFormField('phone', '+380');
      return;
    }
    const numericValue = value.replace(/[^\d+]/g, '');
    const formattedValue = numericValue.startsWith('+') ? numericValue : `+${numericValue}`;
    if (!formattedValue.startsWith('+380')) {
       if (formattedValue.startsWith('+0')) {
         updateFormField('phone', '+380' + formattedValue.substring(2));
       } else {
         updateFormField('phone', '+380');
       }
       return;
    }
    if (formattedValue.length <= 13) {
      updateFormField('phone', formattedValue);
    }
  }, [updateFormField]);

  const handlePhoneFocus = useCallback(() => {
    if (!formData.phone) {
      updateFormField('phone', '+380');
    }
  }, [formData.phone, updateFormField]);

  const validateForm = useCallback((): boolean => {
    const errors: Record<string, string> = {};

    const firstNameValidation = validateName(formData.firstName, "Ім'я");
    if (!firstNameValidation.valid) {
      errors.firstName = firstNameValidation.message;
    }

    const lastNameValidation = validateName(formData.lastName, "Прізвище");
    if (!lastNameValidation.valid) {
      errors.lastName = lastNameValidation.message;
    }

    const phoneValidation = validatePhoneNumber(formData.phone);
    if (!phoneValidation.valid) {
      errors.phone = phoneValidation.message;
    }

    const emailValidation = validateEmail(formData.email);
    if (!emailValidation.valid) {
      errors.email = emailValidation.message;
    }

    if (!bookingDate) {
      errors.date = 'Будь ласка, оберіть дату';
    }

    if (!bookingTime) {
      errors.time = 'Будь ласка, оберіть час';
    }

    if (formData.notes.trim()) {
      const notesValidation = validateNotes(formData.notes);
      if (!notesValidation.valid) {
        errors.notes = notesValidation.message;
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  }, [formData, bookingDate, bookingTime]);

  const handleSubmit = useCallback(() => {
    if (!validateForm()) {
      setError("Будь ласка, заповніть всі обов'язкові поля коректно");
      window.scrollTo({ top: 0, behavior: 'smooth' });
      return;
    }

    const normalizedPhone = normalizePhoneNumber(formData.phone);
    const normalizedEmail = formData.email.trim().toLowerCase();

    setContactInfo({
      firstName: formData.firstName.trim(),
      lastName: formData.lastName.trim(),
      phone: normalizedPhone,
      email: normalizedEmail,
      notes: formData.notes.trim()
    });

    navigate('/clothing');
  }, [validateForm, formData, setContactInfo, navigate]);

  const toggleService = useCallback((service: AdditionalService) => {
    setSelectedServices((prev) =>
      prev.find((s) => s.id === service.id)
        ? prev.filter((s) => s.id !== service.id)
        : [...prev, service]
    );
  }, [setSelectedServices]);

  // 🚀 Мемоїзація розрахунків
  const totalCost = useMemo(() => {
    if (!selectedLocation) return 0;
    const basePrice = parseFloat(selectedLocation.hourlyRate) * durationHours;
    const servicesPrice = selectedServices.reduce((sum, s) => sum + parseFloat(s.price), 0);
    return basePrice + servicesPrice;
  }, [selectedLocation, durationHours, selectedServices]);

  const durationOptions = useMemo(() => {
    if (!settings) return [];
    const minDuration = getMinDuration();
    const maxDuration = settings.maxBookingHours ? parseFloat(settings.maxBookingHours.toString()) : 8;
    const options: number[] = [];
    for (let h = minDuration; h <= maxDuration; h += 0.5) {
      options.push(h);
    }
    return options;
  }, [settings, getMinDuration]);

  if (loading) {
    return <BookingFormSkeleton />;
  }

  if (!settings || !selectedLocation) return null;

  const today = getTodayDate();
  const maxDate = getMaxBookingDate(settings.advanceBookingDays || 30);

  const formatDuration = (hours: number): string => {
    if (hours === 0.5) return '30 хвилин';
    if (hours === 1) return '1 година';
    if (hours === 1.5) return '1.5 години';
    const whole = Math.floor(hours);
    const hasHalf = hours % 1 !== 0;
    if (whole < 5) {
      return hasHalf ? `${whole}.5 години` : `${whole} години`;
    }
    return hasHalf ? `${whole}.5 годин` : `${whole} годин`;
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/')}
              className="flex items-center text-slate-500 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              <span className="font-medium">Назад до студій</span>
            </button>
            <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Бронювання</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        {/* Location Info */}
        <div className="bg-white border border-slate-200 mb-10 shadow-sm">
          <div className="p-8">
            <div className="flex flex-col md:flex-row justify-between md:items-start gap-4 mb-2">
               <div>
                  <h1 className="text-3xl font-bold text-slate-900 mb-2">{selectedLocation.name}</h1>
                  {(selectedLocation as any).address && (
                    <div className="flex items-center text-slate-500 mb-4">
                      <MapPin className="w-4 h-4 mr-2" />
                      <span className="text-sm">{(selectedLocation as any).address}</span>
                    </div>
                  )}
               </div>
               <div className="flex items-center bg-slate-50 px-4 py-2 border border-slate-100">
                  <span className="font-bold text-slate-900 mr-1 text-lg">
                    {formatCurrency(parseFloat(selectedLocation.hourlyRate))}
                  </span>
                  <span className="text-slate-500 text-sm">/ година</span>
               </div>
            </div>
            <p className="text-slate-500 text-sm max-w-2xl">
               Заповніть форму нижче, щоб забронювати цей простір. Оберіть зручний час та додаткові послуги.
            </p>
          </div>
        </div>

        <div className="space-y-10">
          {/* Date and Duration */}
          <section>
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3">
                 <Calendar className="w-4 h-4 text-slate-700" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Дата і тривалість</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Дата
                </label>
                <DatePicker
                  selectedDate={bookingDate}
                  onChange={(date) => {
                    setBookingDate(date);
                    setBookingTime('');
                    setValidationErrors((prev) => ({ ...prev, date: '', time: '' }));
                  }}
                  minDate={today}
                  maxDate={maxDate}
                  error={validationErrors.date}
                />
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Тривалість
                </label>
                <select
                  value={durationHours}
                  onChange={(e) => {
                    setDurationHours(parseFloat(e.target.value));
                    setBookingTime('');
                  }}
                  className="w-full px-5 py-4 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 bg-white font-medium text-slate-900 appearance-none rounded-none"
                >
                  {durationOptions.map((hours) => (
                    <option key={hours} value={hours}>
                      {formatDuration(hours)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Time Slots */}
          {bookingDate && (
            <section className="border-t border-slate-100 pt-10">
              <div className="flex items-center mb-6">
                <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3">
                   <Clock className="w-4 h-4 text-slate-700" />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Оберіть час</h2>
              </div>

              {checkingSlots ? (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                  {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                    <div key={i} className="h-[46px] bg-slate-100 animate-pulse border border-slate-200" />
                  ))}
                </div>
              ) : availableSlots.length === 0 ? (
                <div className="text-center py-8 bg-slate-50 border border-slate-100">
                  <p className="text-slate-600 font-medium">Немає вільних слотів</p>
                  <p className="text-sm text-slate-400 mt-1">Змініть дату або тривалість</p>
                </div>
              ) : (
                <div>
                    <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-3">
                    {availableSlots.map((slot) => {
                        const isPast = isTimeSlotInPast(bookingDate, slot.startTime);
                        const isAvailable = slot.available && !isPast;
                        const isSelected = bookingTime === slot.startTime;

                        return (
                        <button
                            key={slot.startTime}
                            type="button"
                            onClick={() => {
                            if (isAvailable) {
                                setBookingTime(slot.startTime);
                                setValidationErrors((prev) => ({ ...prev, time: '' }));
                            }
                            }}
                            disabled={!isAvailable}
                            className={`px-4 py-3 font-medium text-sm transition-all border rounded-none ${
                            isSelected
                                ? 'bg-slate-900 text-white border-slate-900 shadow-none'
                                : isAvailable
                                ? 'bg-white text-slate-700 border-slate-200 hover:border-slate-400 hover:bg-slate-50'
                                : 'bg-slate-50 text-slate-300 border-slate-100 cursor-not-allowed'
                            }`}
                        >
                            {formatTime(slot.startTime)}
                        </button>
                        );
                    })}
                    </div>
                    {validationErrors.time && (
                    <p className="text-red-600 text-sm mt-3 ml-1">{validationErrors.time}</p>
                    )}
                </div>
              )}
            </section>
          )}

          {/* Additional Services */}
          {services.length > 0 && (
            <section className="border-t border-slate-100 pt-10">
              <div className="flex items-center mb-6">
                 <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3">
                   <Plus className="w-4 h-4 text-slate-700" />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Додаткові послуги</h2>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {services.map((service) => {
                  const isSelected = selectedServices.some((s) => s.id === service.id);
                  return (
                    <div
                      key={service.id}
                      onClick={() => toggleService(service)}
                      className={`group p-5 cursor-pointer transition-all border rounded-none ${
                        isSelected
                          ? 'bg-slate-50 border-slate-900 ring-1 ring-slate-900'
                          : 'bg-white border-slate-200 hover:border-slate-300'
                      }`}
                    >
                      <div className="flex justify-between items-start mb-2">
                        <h3 className="font-bold text-slate-900 text-base">{service.name}</h3>
                        <span className="text-base font-semibold text-slate-900">
                          {formatCurrency(parseFloat(service.price))}
                        </span>
                      </div>
                      <p className="text-sm text-slate-500 mb-2 leading-relaxed">{service.description}</p>
                      {service.durationMinutes > 0 && (
                        <p className="text-xs text-slate-400">
                          + {service.durationMinutes} хв
                        </p>
                      )}
                    </div>
                  );
                })}
              </div>
            </section>
          )}

          {/* Contact Information */}
          <section className="border-t border-slate-100 pt-10 mb-20">
            <div className="flex items-center mb-6">
               <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3">
                   <User className="w-4 h-4 text-slate-700" />
                </div>
              <h2 className="text-xl font-bold text-slate-900">Контакти</h2>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Ім'я
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => updateFormField('firstName', e.target.value)}
                  className={`w-full px-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none ${
                    validationErrors.firstName ? 'border-red-400' : 'border-slate-200'
                  }`}
                  placeholder="Іван"
                />
                {validationErrors.firstName && (
                  <p className="text-red-600 text-sm mt-2 ml-1">{validationErrors.firstName}</p>
                )}
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Прізвище
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => updateFormField('lastName', e.target.value)}
                  className={`w-full px-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none ${
                    validationErrors.lastName ? 'border-red-400' : 'border-slate-200'
                  }`}
                  placeholder="Петренко"
                />
                {validationErrors.lastName && (
                  <p className="text-red-600 text-sm mt-2 ml-1">{validationErrors.lastName}</p>
                )}
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Телефон
                </label>
                <div className="relative">
                  <input
                    type="tel"
                    value={formData.phone}
                    onFocus={handlePhoneFocus}
                    onChange={handlePhoneChange}
                    className={`w-full px-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none tracking-wider font-medium ${
                      validationErrors.phone ? 'border-red-400' : 'border-slate-200'
                    }`}
                    placeholder="+380XXXXXXXXX"
                    maxLength={13}
                  />
                  {formData.phone.length > 4 && formData.phone.length < 13 && (
                     <div className="absolute right-3 top-1/2 -translate-y-1/2 text-xs text-slate-400 pointer-events-none">
                        ще {13 - formData.phone.length} цифр
                     </div>
                  )}
                </div>

                {validationErrors.phone && (
                  <p className="text-red-600 text-sm mt-2 ml-1">{validationErrors.phone}</p>
                )}
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => updateFormField('email', e.target.value)}
                  className={`w-full px-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none ${
                    validationErrors.email ? 'border-red-400' : 'border-slate-200'
                  }`}
                  placeholder="ivan@example.com"
                />
                {validationErrors.email && (
                  <p className="text-red-600 text-sm mt-2 ml-1">{validationErrors.email}</p>
                )}
              </div>
            </div>

            <div className="mt-6">
              <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs">
                Нотатки
              </label>
              <textarea
                value={formData.notes}
                onChange={(e) => updateFormField('notes', e.target.value)}
                rows={3}
                className={`w-full px-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 resize-none rounded-none ${
                  validationErrors.notes ? 'border-red-400' : 'border-slate-200'
                }`}
                placeholder="Додаткові побажання..."
              />
              {validationErrors.notes && (
                <p className="text-red-600 text-sm mt-2 ml-1">{validationErrors.notes}</p>
              )}
            </div>
          </section>
        </div>
      </div>

      {/* Summary Footer */}
      <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4 sm:p-6 z-30">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left">
            <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">До сплати</p>
            <div className="flex items-baseline gap-2 justify-center sm:justify-start">
              <span className="text-3xl font-bold text-slate-900">
                {formatCurrency(totalCost)}
              </span>
              <span className="text-sm text-slate-500">
                за {formatDuration(durationHours)}
              </span>
            </div>
          </div>

          <div className="flex gap-3 w-full sm:w-auto">
             <button
                onClick={() => navigate('/')}
                className="flex-1 sm:flex-none px-6 py-4 text-slate-600 font-medium hover:bg-slate-50 border border-slate-200 hover:border-slate-400 transition-colors rounded-none"
            >
              Скасувати
            </button>
            <button
              onClick={handleSubmit}
              className="flex-1 sm:flex-none bg-slate-900 hover:bg-black text-white px-8 py-4 font-bold transition-all shadow-none hover:shadow-lg flex items-center justify-center rounded-none"
            >
              <span>Далі</span>
              <ChevronRight className="ml-2 w-5 h-5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
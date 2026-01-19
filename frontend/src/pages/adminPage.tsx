import React, { useState, useEffect } from 'react';
import {
  Calendar, Plus, X, Clock, User, MapPin, Phone, Search,
  ChevronLeft, ChevronRight, AlertCircle, Loader2, Check
} from 'lucide-react';
import { clothingService } from '../services/api';

// API Configuration
const API_BASE = '/api';

// === ТИПИ ДАНИХ ===
interface Location {
  id: string;
  name: string;
  hourly_rate: number | string;
}

interface Service {
  id: string;
  name: string;
  price: number | string;
  is_active: boolean;
}

interface ClothingItem {
  id: string;
  name: string;
  category: { id: string; name: string };
  size: string;
  price: string;
  quantity: number;
  primaryImage?: { imageUrl: string };
}

interface Booking {
  id: string;
  location: Location;
  first_name: string;
  last_name: string;
  phone_number: string;
  email: string;
  booking_date: string;
  booking_time: string;
  duration_hours: number;
  status: string;
  total_amount: number;
  deposit_amount: number;
  notes: string;
  additional_services: Service[];
  clothing_items?: Array<{
    clothing_item: ClothingItem;
    quantity: number;
  }>;
}

interface TimeSlot {
  start_time: string;
  end_time: string;
  available: boolean;
}

// === UTILS ===
const formatDate = (date: string) => {
  return new Date(date).toLocaleDateString('uk-UA', {
    day: '2-digit', month: '2-digit', year: 'numeric'
  });
};

const formatTime = (time: string) => time ? time.slice(0, 5) : '';

const formatCurrency = (amount: number | string) => {
  const num = parseFloat(String(amount));
  return isNaN(num) ? '0 ₴' : `${Math.round(num)} ₴`;
};

const getTodayDate = () => new Date().toISOString().split('T')[0];

const addDays = (date: string, days: number) => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result.toISOString().split('T')[0];
};

// API Helper
const fetchAPI = async (url: string, options?: RequestInit) => {
  const token = localStorage.getItem('access_token');
  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...(token && { 'Authorization': `Bearer ${token}` }),
    ...options?.headers,
  };

  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    localStorage.removeItem('access_token');
    window.location.href = '/manager/login';
    throw new Error('Unauthorized');
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(error.error || `HTTP ${response.status}`);
  }

  return response.json();
};

// === ГОЛОВНИЙ КОМПОНЕНТ ===
const AdminBookingPanel = () => {
  const [currentDate, setCurrentDate] = useState(getTodayDate());
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [filteredBookings, setFilteredBookings] = useState<Booking[]>([]);
  const [locations, setLocations] = useState<Location[]>([]);
  const [selectedLocation, setSelectedLocation] = useState('all');
  const [selectedStatus, setSelectedStatus] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => { loadLocations(); }, []);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { loadBookings(); }, [currentDate, selectedLocation]);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { filterBookings(); }, [bookings, selectedStatus, searchQuery]);

  const loadLocations = async () => {
    try {
      const data = await fetchAPI(`${API_BASE}/locations/`);
      setLocations(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadBookings = async () => {
    setLoading(true);
    setError('');
    try {
      const params = new URLSearchParams({ start_date: currentDate, end_date: currentDate });
      if (selectedLocation !== 'all') params.append('location_id', selectedLocation);
      const data = await fetchAPI(`${API_BASE}/bookings/location-bookings/?${params}`);
      setBookings(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Помилка завантаження');
    } finally {
      setLoading(false);
    }
  };

  const filterBookings = () => {
    let filtered = [...bookings];
    if (selectedStatus !== 'all') filtered = filtered.filter(b => b.status === selectedStatus);
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(b =>
        b.first_name.toLowerCase().includes(query) ||
        b.last_name.toLowerCase().includes(query) ||
        b.phone_number.includes(query)
      );
    }
    setFilteredBookings(filtered);
  };


  const handleStatusChange = async (bookingId: string, newStatus: string) => {
    try {
      let endpoint = '';
      if (newStatus === 'paid') endpoint = 'mark-paid';
      else if (newStatus === 'confirmed') endpoint = 'confirm';
      else if (newStatus === 'completed') endpoint = 'complete';
      else if (newStatus === 'cancelled') endpoint = 'cancel';

      if (!endpoint) throw new Error('Unknown status action');

      await fetchAPI(`${API_BASE}/bookings/${bookingId}/${endpoint}/`, { method: 'POST' });
      await loadBookings();
    } catch (err) {
      console.error(err);
      alert('Помилка зміни статусу');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      {/* Header */}
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold text-slate-900">Панель керування бронюваннями</h1>
        <button
          onClick={() => setShowCreateModal(true)}
          disabled={locations.length === 0}
          className="flex items-center gap-2 bg-slate-900 text-white px-4 py-2 rounded-lg hover:bg-black disabled:opacity-50"
        >
          <Plus className="w-4 h-4" />
          Створити бронювання
        </button>
      </div>

      {/* Controls */}
      <div className="mb-6 flex flex-wrap gap-4 items-center bg-white p-4 rounded-lg shadow-sm">
        <div className="flex items-center gap-2">
          <button onClick={() => setCurrentDate(addDays(currentDate, -1))} className="p-1 hover:bg-slate-100 rounded">
            <ChevronLeft className="w-5 h-5" />
          </button>
          <div className="flex items-center gap-2 px-3 py-1 bg-slate-50 rounded">
            <Calendar className="w-4 h-4" />
            <span className="font-medium">{formatDate(currentDate)}</span>
          </div>
          <button onClick={() => setCurrentDate(addDays(currentDate, 1))} className="p-1 hover:bg-slate-100 rounded">
            <ChevronRight className="w-5 h-5" />
          </button>
          <button onClick={() => setCurrentDate(getTodayDate())} className="text-xs px-2 text-slate-500 hover:text-slate-900">
            Сьогодні
          </button>
        </div>

        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Пошук клієнта..."
            className="pl-8 pr-3 py-2 border border-slate-200 rounded text-sm w-full"
          />
        </div>

        <select
          value={selectedLocation}
          onChange={(e) => setSelectedLocation(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded text-sm"
        >
          <option value="all">Всі локації</option>
          {locations.map(l => (
            <option key={l.id} value={l.id}>{l.name}</option>
          ))}
        </select>

        <select
          value={selectedStatus}
          onChange={(e) => setSelectedStatus(e.target.value)}
          className="px-3 py-2 border border-slate-200 rounded text-sm"
        >
          <option value="all">Всі статуси</option>
          <option value="pending_payment">Очікує оплати</option>
          <option value="paid">Оплачено</option>
          <option value="confirmed">Підтверджено</option>
          <option value="completed">Завершено</option>
          <option value="cancelled">Скасовано</option>
        </select>
      </div>

      {/* Content */}
      <div className="space-y-3">
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded flex items-center gap-2">
            <AlertCircle className="w-5 h-5" />
            {error}
          </div>
        )}

        {loading ? (
          <div className="flex justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-slate-400" />
          </div>
        ) : filteredBookings.length === 0 ? (
          <div className="bg-white rounded-lg p-12 text-center text-slate-400">
            Немає бронювань
          </div>
        ) : (
          filteredBookings.map(b => (
            <BookingCard key={b.id} booking={b} onStatusChange={handleStatusChange} />
          ))
        )}
      </div>

      {showCreateModal && (
        <CreateBookingModal
          locations={locations}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => { setShowCreateModal(false); loadBookings(); }}
        />
      )}
    </div>
  );
};

// === КАРТКА БРОНЮВАННЯ ===
const BookingCard: React.FC<{ booking: Booking; onStatusChange: (id: string, s: string) => void }> = ({ booking, onStatusChange }) => {
  const [expanded, setExpanded] = useState(false);

  const statusColors: Record<string, string> = {
    pending_payment: 'bg-yellow-100 text-yellow-800',
    paid: 'bg-blue-100 text-blue-800',
    confirmed: 'bg-green-100 text-green-800',
    completed: 'bg-slate-100 text-slate-600',
    cancelled: 'bg-red-100 text-red-800'
  };

  const getEndTime = (time: string, duration: number) => {
    if (!time) return '';
    const [h, m] = time.split(':').map(Number);
    const durationMinutes = Math.round(duration * 60);
    const total = h * 60 + m + durationMinutes;
    const endH = Math.floor(total / 60) % 24;
    const endM = total % 60;
    return `${String(endH).padStart(2, '0')}:${String(endM).padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm overflow-hidden">
      <div onClick={() => setExpanded(!expanded)} className="p-4 cursor-pointer flex items-center justify-between hover:bg-slate-50">
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-2 text-sm font-mono">
            <Clock className="w-4 h-4 text-slate-400" />
            {formatTime(booking.booking_time)} - {getEndTime(booking.booking_time, booking.duration_hours)}
          </div>
          <div className="flex items-center gap-2">
            <User className="w-4 h-4 text-slate-400" />
            <span className="font-medium">{booking.first_name} {booking.last_name}</span>
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <MapPin className="w-4 h-4" />
            {booking.location.name}
          </div>
          <div className="flex items-center gap-2 text-sm text-slate-600">
            <Phone className="w-4 h-4" />
            {booking.phone_number}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <span className={`px-3 py-1 rounded-full text-xs font-medium ${statusColors[booking.status]}`}>
            {booking.status}
          </span>
          <span className="font-bold text-lg">{formatCurrency(booking.total_amount)}</span>
        </div>
      </div>

      {expanded && (
        <div className="border-t p-4 bg-slate-50 space-y-4">
          <div className="bg-white p-4 rounded">
            <h4 className="font-semibold mb-3">Деталі оплати</h4>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span>Оренда ({booking.duration_hours} год):</span>
                <span>{formatCurrency(parseFloat(String(booking.location.hourly_rate)) * booking.duration_hours)}</span>
              </div>
              {booking.additional_services.map(s => (
                <div key={s.id} className="flex justify-between text-slate-600">
                  <span>{s.name}:</span>
                  <span>{formatCurrency(s.price)}</span>
                </div>
              ))}
              {booking.clothing_items && booking.clothing_items.length > 0 && (
                <>
                  <div className="pt-2 border-t font-medium">Одяг:</div>
                  {booking.clothing_items.map((item: { clothing_item: ClothingItem; quantity: number }, idx: number) => (
                    <div key={idx} className="flex justify-between text-slate-600 pl-4">
                      <span>{item.clothing_item?.name || 'Item'} x{item.quantity}</span>
                      <span>{formatCurrency(parseFloat(item.clothing_item?.price || '0') * item.quantity)}</span>
                    </div>
                  ))}
                </>
              )}
              <div className="pt-2 border-t flex justify-between font-bold">
                <span>Всього:</span>
                <span>{formatCurrency(booking.total_amount)}</span>
              </div>
            </div>
          </div>

          <div className="bg-white p-4 rounded">
            <h4 className="font-semibold mb-3">Управління</h4>
            <div className="flex flex-wrap gap-2">
              {booking.status === 'pending_payment' && (
                <button onClick={() => onStatusChange(booking.id, 'paid')} className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-sm">
                  Сплачено
                </button>
              )}
              {booking.status === 'paid' && (
                <button onClick={() => onStatusChange(booking.id, 'confirmed')} className="bg-green-600 text-white px-3 py-1 rounded hover:bg-green-700 text-sm">
                  Підтвердити
                </button>
              )}
              {booking.status === 'confirmed' && (
                <button onClick={() => onStatusChange(booking.id, 'completed')} className="bg-slate-800 text-white px-3 py-1 rounded hover:bg-black text-sm">
                  Завершити
                </button>
              )}
              <button
                onClick={() => { if(confirm('Скасувати?')) onStatusChange(booking.id, 'cancelled'); }}
                className="border border-red-300 text-red-600 px-3 py-1 rounded hover:bg-red-50 text-sm"
              >
                Скасувати
              </button>
            </div>
          </div>

          {booking.notes && (
            <div className="bg-white p-4 rounded">
              <h4 className="font-semibold mb-2">Нотатки:</h4>
              <p className="text-sm text-slate-600">{booking.notes}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

// === CREATE BOOKING MODAL ===
const CreateBookingModal: React.FC<{
  locations: Location[];
  onClose: () => void;
  onSuccess: () => void
}> = ({ locations, onClose, onSuccess }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [services, setServices] = useState<Service[]>([]);
  const [availableSlots, setAvailableSlots] = useState<TimeSlot[]>([]);
  const [loadingSlots, setLoadingSlots] = useState(false);

  // Clothing State
  const [clothingItems, setClothingItems] = useState<ClothingItem[]>([]);
  const [clothingCart, setClothingCart] = useState<{ item: ClothingItem; quantity: number }[]>([]);
  const [clothingSearch, setClothingSearch] = useState('');
  const [loadingClothing, setLoadingClothing] = useState(false);

  // Form Data
  const [formData, setFormData] = useState({
    locationId: '',
    bookingDate: getTodayDate(),
    bookingTime: '',
    durationHours: 1,
    firstName: '',
    lastName: '',
    phoneNumber: '',
    email: '',
    notes: '',
    additionalServiceIds: [] as string[],
    status: 'confirmed'
  });

  // Loaders
  useEffect(() => {
    fetchAPI(`${API_BASE}/services/`)
      .then((data: Service[]) => setServices(data.filter((s: Service) => s.is_active)))
      .catch(console.error);

    setLoadingClothing(true);
    clothingService.getItems({ availableOnly: true })
      .then(items => setClothingItems(items))
      .catch(console.error)
      .finally(() => setLoadingClothing(false));
  }, []);

  useEffect(() => {
    if (formData.locationId && formData.bookingDate) {
      setLoadingSlots(true);
      fetchAPI(`${API_BASE}/bookings/availability/check-availability/`, {
        method: 'POST',
        body: JSON.stringify({
          date: formData.bookingDate,
          duration_hours: formData.durationHours,
          location_id: formData.locationId
        })
      })
        .then(res => setAvailableSlots(res.slots))
        .catch(() => setAvailableSlots([]))
        .finally(() => setLoadingSlots(false));
    }
  }, [formData.locationId, formData.bookingDate, formData.durationHours]);

  // Validation
  const validateStep = (currentStep: number) => {
    if (currentStep === 1) return formData.locationId && formData.bookingDate && formData.bookingTime;
    if (currentStep === 2) return formData.firstName && formData.phoneNumber;
    return true;
  };

  // Clothing Logic
  const addToCart = (item: ClothingItem) => {
    const existing = clothingCart.find(c => c.item.id === item.id);
    const currentQty = existing ? existing.quantity : 0;
    if (currentQty >= item.quantity) return;

    if (existing) {
      setClothingCart(prev => prev.map(c =>
        c.item.id === item.id ? { ...c, quantity: c.quantity + 1 } : c
      ));
    } else {
      setClothingCart(prev => [...prev, { item, quantity: 1 }]);
    }
  };

  const removeFromCart = (itemId: string) => {
    const existing = clothingCart.find(c => c.item.id === itemId);
    if (!existing) return;

    if (existing.quantity > 1) {
      setClothingCart(prev => prev.map(c =>
        c.item.id === itemId ? { ...c, quantity: c.quantity - 1 } : c
      ));
    } else {
      setClothingCart(prev => prev.filter(c => c.item.id !== itemId));
    }
  };


  const calculateEstimatedTotal = () => {
    const loc = locations.find(l => l.id === formData.locationId);
    if (!loc) return 0;

    const hourlyRate = parseFloat(String(loc.hourly_rate)) || 0;
    const base = hourlyRate * formData.durationHours;

    const serv = services
      .filter(s => formData.additionalServiceIds.includes(s.id))
      .reduce((acc, s) => acc + (parseFloat(String(s.price)) || 0), 0);

    const cloth = clothingCart.reduce((acc, c) =>
      acc + (parseFloat(String(c.item.price)) || 0) * c.quantity, 0
    );

    return base + serv + cloth;
  };

  const handleSubmit = async () => {
    setLoading(true);
    try {
      const payload = {
        location_id: formData.locationId,
        booking_date: formData.bookingDate,
        booking_time: formData.bookingTime,
        duration_hours: formData.durationHours,
        first_name: formData.firstName,
        last_name: formData.lastName,
        phone_number: formData.phoneNumber,
        email: formData.email,
        notes: formData.notes,
        status: formData.status,
        additional_service_ids: formData.additionalServiceIds,
        clothing_items: clothingCart.map(c => ({
          clothing_item_id: c.item.id,
          quantity: c.quantity
        })),
      };

      console.log('📤 Sending admin booking request:', payload);

      const response = await fetchAPI(`${API_BASE}/bookings/admin-create/`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      console.log('✅ Booking created:', response);
      onSuccess();
    } catch (err) {
      console.error('❌ Booking creation failed:', err);
      alert(err instanceof Error ? err.message : 'Помилка створення бронювання');
    } finally {
      setLoading(false);
    }
  };

  const filteredClothing = clothingItems.filter(i =>
    i.name.toLowerCase().includes(clothingSearch.toLowerCase())
  );

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b p-4 flex items-center justify-between">
          <h2 className="text-xl font-bold">Створити бронювання (Крок {step}/4)</h2>
          <button onClick={onClose} className="p-1 hover:bg-slate-100 rounded">
            <X className="w-5 h-5" />
          </button>
        </div>

        <div className="p-6 space-y-6">
          {/* STEP 1: Локація, дата, час */}
          {step === 1 && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">Локація</label>
                <select
                  value={formData.locationId}
                  onChange={(e) => setFormData({...formData, locationId: e.target.value, bookingTime: ''})}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="">Оберіть...</option>
                  {locations.map(l => (
                    <option key={l.id} value={l.id}>
                      {l.name} ({formatCurrency(l.hourly_rate)}/год)
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Дата</label>
                <input
                  type="date"
                  value={formData.bookingDate}
                  onChange={(e) => setFormData({...formData, bookingDate: e.target.value, bookingTime: ''})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Тривалість</label>
                <select
                  value={formData.durationHours}
                  onChange={(e) => setFormData({...formData, durationHours: Number(e.target.value), bookingTime: ''})}
                  className="w-full px-3 py-2 border rounded"
                >
                  {Array.from({ length: 16 }, (_, i) => (i + 1) / 2).map((h) => (
                    <option key={h} value={h}>{h % 1 === 0 ? `${Math.round(h)} год` : `${h} год`}</option>
                  ))}
                </select>
              </div>

              {formData.locationId && (
                <div>
                  <label className="block text-sm font-medium mb-2">Час</label>
                  {loadingSlots ? (
                    <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                  ) : (
                    <div className="grid grid-cols-4 gap-2">
                      {availableSlots.map(s => (
                        <button
                          key={s.start_time}
                          onClick={() => s.available && setFormData({...formData, bookingTime: s.start_time})}
                          disabled={!s.available}
                          className={`p-2 text-sm border rounded ${
                            formData.bookingTime === s.start_time
                              ? 'bg-black text-white'
                              : s.available
                              ? 'hover:bg-slate-100'
                              : 'opacity-30 cursor-not-allowed'
                          }`}
                        >
                          {formatTime(s.start_time)}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </>
          )}

          {/* STEP 2: Дані клієнта */}
          {step === 2 && (
            <>
              <div>
                <label className="block text-sm font-medium mb-2">Ім'я</label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => setFormData({...formData, firstName: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Прізвище</label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => setFormData({...formData, lastName: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Телефон</label>
                <input
                  type="tel"
                  value={formData.phoneNumber}
                  onChange={(e) => setFormData({...formData, phoneNumber: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Email</label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Нотатки</label>
                <textarea
                  value={formData.notes}
                  onChange={(e) => setFormData({...formData, notes: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                  rows={3}
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">Статус</label>
                <select
                  value={formData.status}
                  onChange={(e) => setFormData({...formData, status: e.target.value})}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="confirmed">Підтверджено</option>
                  <option value="paid">Оплачено</option>
                  <option value="pending_payment">Очікує оплати</option>
                </select>
              </div>
            </>
          )}

          {/* STEP 3: Послуги та одяг */}
          {step === 3 && (
            <>
              <div>
                <h3 className="font-semibold mb-3">Послуги</h3>
                <div className="space-y-2">
                  {services.map(s => (
                    <label key={s.id} className="flex items-center gap-2 p-2 hover:bg-slate-50 rounded cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.additionalServiceIds.includes(s.id)}
                        onChange={(e) => {
                          const ids = e.target.checked
                            ? [...formData.additionalServiceIds, s.id]
                            : formData.additionalServiceIds.filter(id => id !== s.id);
                          setFormData({...formData, additionalServiceIds: ids});
                        }}
                      />
                      <span>{s.name} ({formatCurrency(s.price)})</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="font-semibold mb-3">Оренда одягу</h3>
                <input
                  type="text"
                  value={clothingSearch}
                  onChange={(e) => setClothingSearch(e.target.value)}
                  placeholder="Пошук одягу..."
                  className="w-full px-3 py-2 border rounded mb-3"
                />

                {loadingClothing ? (
                  <Loader2 className="w-6 h-6 animate-spin mx-auto" />
                ) : (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {filteredClothing.map(item => {
                      const inCart = clothingCart.find(c => c.item.id === item.id)?.quantity || 0;
                      return (
                        <div key={item.id} className="flex items-center justify-between p-3 border rounded hover:bg-slate-50">
                          <div>
                            <div className="font-medium">{item.name}</div>
                            <div className="text-sm text-slate-500">
                              {item.size} • {formatCurrency(item.price)}
                            </div>
                            <div className="text-xs text-slate-400">Склад: {item.quantity}</div>
                          </div>
                          <div className="flex items-center gap-2">
                            {inCart > 0 && (
                              <button
                                onClick={() => removeFromCart(item.id)}
                                className="w-6 h-6 bg-slate-100 hover:bg-slate-200 rounded flex items-center justify-center"
                              >
                                -
                              </button>
                            )}
                            {inCart > 0 && <span className="w-6 text-center">{inCart}</span>}
                            <button
                              onClick={() => addToCart(item)}
                              disabled={inCart >= item.quantity}
                              className="w-6 h-6 bg-slate-900 text-white hover:bg-black rounded flex items-center justify-center disabled:opacity-50"
                            >
                              +
                            </button>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </>
          )}

          {/* STEP 4: Фінальний розрахунок - ✅ ВИПРАВЛЕНО */}
          {step === 4 && (
            <>
              <div className="p-6 bg-white rounded-lg border">
                <h3 className="font-semibold mb-4">Фінальний розрахунок</h3>

                {/* ✅ ВИПРАВЛЕНО: Оренда з parseFloat */}
                <div className="flex justify-between mb-2">
                  <span>Оренда ({formData.durationHours} год):</span>
                  <span>{formatCurrency(
                    (() => {
                      const selectedLoc = locations.find(l => l.id === formData.locationId);
                      const hourlyRate = selectedLoc ? (parseFloat(String(selectedLoc.hourly_rate)) || 0) : 0;
                      return hourlyRate * formData.durationHours;
                    })()
                  )}</span>
                </div>

                {/* ✅ ВИПРАВЛЕНО: Послуги з parseFloat */}
                {formData.additionalServiceIds.length > 0 && (
                  <div className="flex justify-between mb-2 text-sm text-gray-600">
                    <span>Послуги:</span>
                    <span>{formatCurrency(
                      services
                        .filter(s => formData.additionalServiceIds.includes(s.id))
                        .reduce((acc, s) => acc + (parseFloat(String(s.price)) || 0), 0)
                    )}</span>
                  </div>
                )}

                {/* ✅ ВИПРАВЛЕНО: Одяг з parseFloat */}
                {clothingCart.length > 0 && (
                  <div className="flex justify-between mb-2 text-sm text-gray-600">
                    <span>Оренда одягу ({clothingCart.reduce((a,c)=>a+c.quantity,0)} шт):</span>
                    <span>{formatCurrency(
                      clothingCart.reduce((acc, c) =>
                        acc + ((parseFloat(String(c.item.price)) || 0) * c.quantity), 0
                      )
                    )}</span>
                  </div>
                )}

                <div className="border-t pt-3 mt-3">
                  <div className="flex justify-between font-bold text-lg">
                    <span>Загальна вартість:</span>
                    <span>{formatCurrency(calculateEstimatedTotal())}</span>
                  </div>
                  <div className="flex justify-between text-sm text-gray-600 mt-2">
                    <span>Депозит (30%):</span>
                    <span>{formatCurrency(calculateEstimatedTotal() * 0.3)}</span>
                  </div>
                </div>
              </div>

              <div className="p-4 bg-gray-50 rounded text-sm space-y-1">
                <div><strong>Клієнт:</strong> {formData.firstName} {formData.lastName}</div>
                <div><strong>Телефон:</strong> {formData.phoneNumber}</div>
                <div><strong>Дата:</strong> {formatDate(formData.bookingDate)} о {formData.bookingTime}</div>
                <div><strong>Локація:</strong> {locations.find(l=>l.id===formData.locationId)?.name}</div>
              </div>
            </>
          )}
        </div>

        {/* Footer buttons */}
        <div className="sticky bottom-0 bg-white border-t p-4 flex gap-3">
          <button
            onClick={() => setStep(s => Math.max(1, s - 1))}
            disabled={step === 1}
            className="px-4 py-2 border rounded hover:bg-slate-50 disabled:opacity-50"
          >
            Назад
          </button>
          {step < 4 ? (
            <button
              onClick={() => {
                if(validateStep(step)) setStep(s => s + 1);
                else alert("Заповніть обов'язкові поля");
              }}
              className="flex-1 px-4 py-2 bg-slate-900 text-white rounded hover:bg-black"
            >
              Далі
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-slate-900 text-white rounded hover:bg-black disabled:opacity-50 flex items-center justify-center gap-2"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Check className="w-4 h-4" />}
              Створити бронювання
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default AdminBookingPanel;

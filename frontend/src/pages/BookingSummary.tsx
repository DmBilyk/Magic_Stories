import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  ArrowLeft,
  MapPin,
  Calendar,
  Clock,
  User,
  Mail,
  Phone,
  CreditCard,
  Check,
  Info,
} from 'lucide-react';
import { useBooking, ContactInfo } from '../context/BookingContext';
import { bookingService } from '../services/api';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { formatCurrency, formatDate, formatTimeRange } from '../utils/dateTime';

export const BookingSummary = () => {
  const navigate = useNavigate();
  const {
    selectedLocation,
    bookingDate,
    bookingTime,
    durationHours,
    selectedServices,
    clothingCart,
    resetBooking,
    contactInfo,
    setContactInfo,
  } = useBooking();

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [bookingComplete, setBookingComplete] = useState(false);

  const [formData, setFormData] = useState<ContactInfo>({
    firstName: contactInfo.firstName,
    lastName: contactInfo.lastName,
    phone: contactInfo.phone,
    email: contactInfo.email,
    notes: contactInfo.notes,
  });

  useEffect(() => {
    if (!selectedLocation || !bookingDate || !bookingTime) {
      navigate('/booking');
      return;
    }
  }, [selectedLocation, bookingDate, bookingTime, navigate]);

  const handleInputChange = (field: keyof ContactInfo, value: string) => {
    const newData = { ...formData, [field]: value };
    setFormData(newData);
    setContactInfo(newData);
  };

  const calculateTotals = () => {
    const baseCost =
      parseFloat(selectedLocation?.hourlyRate || '0') * durationHours;

    const servicesCost = selectedServices.reduce(
      (sum, service) => sum + parseFloat(service.price),
      0
    );

    const clothingCost = clothingCart.reduce(
      (sum, item) => sum + parseFloat(item.item.price) * item.quantity,
      0
    );

    const propsCost = 0;

    const totalAmount = baseCost + servicesCost + clothingCost + propsCost;
    const depositAmount = totalAmount * 0.3;

    return {
      baseCost,
      servicesCost,
      clothingCost,
      totalAmount,
      depositAmount,
    };
  };

  const totals = calculateTotals();

  const handleConfirmBooking = async () => {
    if (!selectedLocation) return;

    setLoading(true);
    setError('');

    try {
      // Переконуємося що час має правильний формат (HH:MM або HH:MM:SS)
      const formattedTime = bookingTime.length === 5 ? bookingTime : bookingTime.substring(0, 5);

      // Формуємо clothing_items тільки якщо є елементи в кошику
      const clothingItemsData = clothingCart.length > 0
        ? clothingCart.map((item) => ({
            clothing_item_id: item.item.id, // <--- ЗМІНЕНО: додано _id
            quantity: item.quantity,
          }))
        : undefined; // Не надсилаємо порожній масив

      const bookingRequest = {
        locationId: selectedLocation.id,      // було location_id
        firstName: formData.firstName,        // було first_name
        lastName: formData.lastName,          // було last_name
        phoneNumber: formData.phone,          // було phone_number
        email: formData.email,
        bookingDate: bookingDate,             // було booking_date
        bookingTime: formattedTime,           // було booking_time
        durationHours: durationHours,         // було duration_hours
        additionalServiceIds: selectedServices.map((s) => s.id), // було additional_service_ids
        clothingItems: clothingItemsData,     // передаємо виправлений масив
        notes: formData.notes || '',
      };

      console.log('Sending correct request:', bookingRequest);
      const response = await bookingService.create(bookingRequest);

      console.log('Received response:', response);

      // Перевіряємо наявність платіжних даних
      if (response.payment?.liqpay_data?.data && response.payment?.liqpay_data?.signature) {
        console.log('LiqPay data found, redirecting to payment...');

        // Створюємо форму для редіректу на LiqPay
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = 'https://www.liqpay.ua/api/3/checkout';
        form.acceptCharset = 'utf-8';
        form.style.display = 'none'; // Приховуємо форму

        // Додаємо поле data
        const dataInput = document.createElement('input');
        dataInput.type = 'hidden';
        dataInput.name = 'data';
        dataInput.value = response.payment.liqpay_data.data;
        form.appendChild(dataInput);

        // Додаємо поле signature
        const signatureInput = document.createElement('input');
        signatureInput.type = 'hidden';
        signatureInput.name = 'signature';
        signatureInput.value = response.payment.liqpay_data.signature;
        form.appendChild(signatureInput);

        // Додаємо форму до body
        document.body.appendChild(form);

        // Додаємо невелику затримку для гарантії, що форма в DOM
        setTimeout(() => {
          console.log('Submitting form to LiqPay...');
          form.submit();
        }, 100);
      } else {
        console.warn('No LiqPay data in response, showing success directly');
        setBookingComplete(true);
        setTimeout(() => {
          resetBooking();
          navigate('/');
        }, 3000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create booking');
      setLoading(false);
    }
  };

  if (bookingComplete) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans">
        <div className="bg-white border border-slate-200 shadow-sm p-12 text-center max-w-md w-full rounded-none">
          <div className="w-20 h-20 bg-green-50 flex items-center justify-center mx-auto mb-6 rounded-none">
            <Check className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900 mb-4">Бронювання успішне!</h1>
          <p className="text-slate-600 mb-6 leading-relaxed">
            Ваше бронювання підтверджено. Ви отримаєте лист з підтвердженням найближчим часом.
          </p>
          <p className="text-sm text-slate-400 uppercase tracking-wide">Повертаємось на головну...</p>
        </div>
      </div>
    );
  }

  if (!selectedLocation) return null;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Header */}
      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between">
            <button
              onClick={() => navigate('/clothing')}
              className="flex items-center text-slate-500 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              <span className="font-medium">Назад до одягу</span>
            </button>
            <span className="text-sm font-semibold text-slate-400 uppercase tracking-wider">Підсумок</span>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        {error && (
          <div className="mb-6">
            <ErrorMessage message={error} />
          </div>
        )}

        <h1 className="text-3xl font-bold text-slate-900 mb-10">Перевірка даних</h1>

        <div className="space-y-10">
          {/* Studio Details Section */}
          <section className="bg-white border border-slate-200 p-8 shadow-sm rounded-none">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3 rounded-none">
                <MapPin className="w-4 h-4 text-slate-700" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Деталі студії</h2>
            </div>

            <div className="space-y-4 ml-0 sm:ml-11">
              <div>
                <p className="text-lg font-bold text-slate-900">{selectedLocation.name}</p>
                {selectedLocation.address && (
                  <p className="text-slate-500 mt-1">{selectedLocation.address}</p>
                )}
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-100">
                <div className="flex items-center">
                  <Calendar className="w-5 h-5 text-slate-400 mr-3 flex-shrink-0" />
                  <p className="text-slate-900 font-medium">{formatDate(bookingDate)}</p>
                </div>
                <div className="flex items-center">
                  <Clock className="w-5 h-5 text-slate-400 mr-3 flex-shrink-0" />
                  <p className="text-slate-900 font-medium">
                    {formatTimeRange(bookingTime, durationHours)}
                    <span className="text-slate-500 ml-2 font-normal">
                      ({durationHours} {durationHours === 1 ? 'година' : 'годин'})
                    </span>
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Contact Information Section */}
          <section className="bg-white border border-slate-200 p-8 shadow-sm rounded-none">
            <div className="flex items-center mb-6">
              <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3 rounded-none">
                <User className="w-4 h-4 text-slate-700" />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Контактна інформація</h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs flex items-center">
                  <User className="w-3 h-3 mr-2 text-slate-400" /> Ім'я
                </label>
                <input
                  type="text"
                  value={formData.firstName}
                  onChange={(e) => handleInputChange('firstName', e.target.value)}
                  className="w-full px-5 py-4 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none bg-slate-50"
                  required
                />
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs flex items-center">
                  <User className="w-3 h-3 mr-2 text-slate-400" /> Прізвище
                </label>
                <input
                  type="text"
                  value={formData.lastName}
                  onChange={(e) => handleInputChange('lastName', e.target.value)}
                  className="w-full px-5 py-4 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none bg-slate-50"
                  required
                />
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs flex items-center">
                  <Phone className="w-3 h-3 mr-2 text-slate-400" /> Телефон
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => handleInputChange('phone', e.target.value)}
                  className="w-full px-5 py-4 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none bg-slate-50"
                  required
                />
              </div>

              <div>
                <label className="text-sm font-semibold text-slate-700 mb-2 block uppercase tracking-wide text-xs flex items-center">
                  <Mail className="w-3 h-3 mr-2 text-slate-400" /> Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => handleInputChange('email', e.target.value)}
                  className="w-full px-5 py-4 border border-slate-200 focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none bg-slate-50"
                  required
                />
              </div>
            </div>
          </section>

          {/* Cost Section */}
          <section className="bg-white border border-slate-200 shadow-sm rounded-none">
             <div className="p-8 border-b border-slate-100">
                <div className="flex items-center mb-6">
                    <div className="w-8 h-8 bg-slate-100 flex items-center justify-center mr-3 rounded-none">
                        <CreditCard className="w-4 h-4 text-slate-700" />
                    </div>
                    <h2 className="text-xl font-bold text-slate-900">Розрахунок вартості</h2>
                </div>

                <div className="space-y-4">
                    <div className="flex justify-between items-baseline">
                        <span className="text-slate-600">
                            Оренда студії <span className="text-slate-400 text-sm">({durationHours} год × {formatCurrency(selectedLocation.hourlyRate)})</span>
                        </span>
                        <span className="font-semibold text-slate-900">
                            {formatCurrency(totals.baseCost)}
                        </span>
                    </div>

                    {selectedServices.length > 0 && (
                        <div className="pt-4 border-t border-slate-100">
                            <div className="flex justify-between mb-3">
                                <span className="text-slate-600 font-medium">Додаткові послуги</span>
                                <span className="font-semibold text-slate-900">{formatCurrency(totals.servicesCost)}</span>
                            </div>
                            <ul className="space-y-2">
                                {selectedServices.map((service) => (
                                <li key={service.id} className="flex justify-between text-sm text-slate-500 pl-4 border-l-2 border-slate-100">
                                    <span>{service.name}</span>
                                    <span>{formatCurrency(service.price)}</span>
                                </li>
                                ))}
                            </ul>
                        </div>
                    )}

                    {clothingCart.length > 0 && (
                        <div className="pt-4 border-t border-slate-100">
                             <div className="flex justify-between mb-3">
                                <span className="text-slate-600 font-medium">Оренда одягу</span>
                                <span className="font-semibold text-slate-900">{formatCurrency(totals.clothingCost)}</span>
                            </div>
                            <ul className="space-y-2">
                                {clothingCart.map((item) => (
                                <li key={item.item.id} className="flex justify-between text-sm text-slate-500 pl-4 border-l-2 border-slate-100">
                                    <span>{item.item.name} <span className="text-slate-400">×{item.quantity}</span></span>
                                    <span>{formatCurrency(parseFloat(item.item.price) * item.quantity)}</span>
                                </li>
                                ))}
                            </ul>
                        </div>
                    )}
                </div>
            </div>

            <div className="bg-slate-50 p-8">
                 <div className="flex justify-between items-end mb-2">
                    <span className="text-sm uppercase tracking-wider font-bold text-slate-500">Загальна сума</span>
                    <span className="text-3xl font-bold text-slate-900">{formatCurrency(totals.totalAmount)}</span>
                 </div>
                 <div className="flex justify-between items-center pt-4 border-t border-slate-200">
                    <span className="font-semibold text-slate-900 flex items-center">
                        <Check className="w-4 h-4 mr-2 text-slate-900" />
                        Необхідна передоплата (30%)
                    </span>
                    <span className="font-bold text-xl text-slate-900">
                        {formatCurrency(totals.depositAmount)}
                    </span>
                 </div>
            </div>
          </section>

           {/* Info Box */}
           <div className="flex items-start bg-white border border-slate-200 p-6 rounded-none">
              <Info className="w-5 h-5 text-slate-400 mr-4 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-slate-500 leading-relaxed">
                <p className="font-semibold text-slate-900 mb-1">Інформація про оплату</p>
                <p>
                  Ви будете перенаправлені на LiqPay для безпечної оплати. Для підтвердження бронювання
                  необхідна передоплата 30%. Залишок можна сплатити у студії.
                </p>
              </div>
            </div>
        </div>
      </div>

      {/* Sticky Footer */}
      <div className="sticky bottom-0 bg-white border-t border-slate-200 p-4 sm:p-6 z-30">
        <div className="max-w-4xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="text-center sm:text-left hidden sm:block">
            <p className="text-slate-500 text-xs uppercase tracking-wider mb-1">До сплати зараз</p>
            <div className="font-bold text-2xl text-slate-900">
                {formatCurrency(totals.depositAmount)}
            </div>
          </div>

          <div className="flex gap-3 w-full sm:w-auto">
             <button
                onClick={() => navigate('/clothing')}
                className="flex-1 sm:flex-none px-6 py-4 text-slate-600 font-medium hover:bg-slate-50 border border-slate-200 hover:border-slate-400 transition-colors rounded-none"
                disabled={loading}
            >
              Назад
            </button>
            <button
              onClick={handleConfirmBooking}
              disabled={
                loading ||
                !formData.firstName ||
                !formData.lastName ||
                !formData.phone ||
                !formData.email
              }
              className="flex-1 sm:flex-none bg-slate-900 hover:bg-black text-white px-8 py-4 font-bold transition-all shadow-none hover:shadow-lg flex items-center justify-center rounded-none disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <LoadingSpinner size="sm" />
                  <span className="ml-2">Обробка...</span>
                </>
              ) : (
                <>
                  <CreditCard className="w-5 h-5 mr-2" />
                  Сплатити та забронювати
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
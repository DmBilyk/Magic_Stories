import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { Check, Home, ArrowRight, MapPin, Calendar, Clock, Loader2, AlertCircle } from 'lucide-react';
import { useBooking } from '../context/BookingContext';
import { paymentService } from '../services/api';; // Імпортуйте новий сервіс
import { formatDate } from '../utils/dateTime'; // Прибираємо formatTimeRange, бо з бекенду прийде чистий час

export const PaymentSuccessPage = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { resetBooking } = useBooking();

  // Локальний стан для даних, завантажених з серверу
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [confirmedBooking, setConfirmedBooking] = useState<any>(null);

  const paymentId = searchParams.get('payment_id');

  useEffect(() => {

  resetBooking();


  let isSubscribed = true;

  const verifyPayment = async () => {
    if (!paymentId || !isSubscribed) return;

    try {
      setLoading(true);
      const data = await paymentService.checkStatus(paymentId);

      if (isSubscribed) {
        if (data.success && data.booking) {
          setConfirmedBooking(data.booking);
        }
        setLoading(false);
      }
    } catch (err) {
      if (isSubscribed) {
        console.error('Failed to verify:', err);
        setError('Помилка перевірки статусу');
        setLoading(false);
      }
    }
  };

  verifyPayment();


    return () => { isSubscribed = false; };

  }, [paymentId]);

  const handleExit = (path: string) => {
    navigate(path);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-slate-900 animate-spin mx-auto mb-4" />
          <p className="text-slate-600">Перевіряємо статус оплати...</p>
        </div>
      </div>
    );
  }

  // Якщо немає ID в URL або помилка завантаження
  if (!paymentId && !confirmedBooking) {
    return (
       <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
         <div className="bg-white p-8 max-w-md w-full text-center border border-slate-200">
            <AlertCircle className="w-12 h-12 text-yellow-500 mx-auto mb-4" />
            <h2 className="text-xl font-bold mb-2">Статус невідомий</h2>
            <p className="text-slate-600 mb-6">Ми не отримали ідентифікатор платежу. Перевірте пошту для підтвердження.</p>
            <button onClick={() => navigate('/')} className="bg-slate-900 text-white px-6 py-3 w-full">На головну</button>
         </div>
       </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center font-sans p-4">
      <div className="bg-white border border-slate-200 shadow-sm p-8 sm:p-12 text-center max-w-md w-full rounded-none">

        {/* Іконка успіху */}
        <div className="w-20 h-20 bg-green-50 flex items-center justify-center mx-auto mb-8 rounded-none border border-green-100">
          <Check className="w-10 h-10 text-green-600" />
        </div>

        <h1 className="text-3xl font-bold text-slate-900 mb-4">
          Оплата успішна!
        </h1>

        <p className="text-slate-600 mb-8 leading-relaxed">
          Дякуємо, {confirmedBooking?.first_name || 'клієнте'}! Ваше бронювання підтверджено. Ми відправили деталі та чек на вашу електронну пошту.
        </p>

        {/* Блок з деталями замовлення (відображаємо тільки якщо завантажили дані) */}
        {confirmedBooking && (
          <div className="bg-slate-50 border border-slate-100 p-6 mb-8 text-left">
            <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-4 border-b border-slate-200 pb-2">
              Деталі бронювання #{confirmedBooking.id.slice(0, 8)}
            </h3>

            <div className="space-y-3">
              {/* Дата */}
              <div className="flex items-center">
                <Calendar className="w-5 h-5 text-slate-400 mr-3 flex-shrink-0" />
                <p className="text-slate-700 font-medium text-sm">
                  {formatDate(confirmedBooking.booking_date)}
                </p>
              </div>

              {/* Час */}
              <div className="flex items-center">
                <Clock className="w-5 h-5 text-slate-400 mr-3 flex-shrink-0" />
                <p className="text-slate-700 font-medium text-sm">
                  {confirmedBooking.booking_time}
                </p>
              </div>

              <div className="mt-2 text-xs text-green-600 font-semibold flex items-center">
                 <Check className="w-3 h-3 mr-1" /> Статус: {confirmedBooking.status === 'paid' ? 'Оплачено' : confirmedBooking.status}
              </div>
            </div>
          </div>
        )}

        {error && (
            <p className="text-sm text-yellow-600 mb-6 bg-yellow-50 p-3">{error}</p>
        )}

        {/* Кнопки навігації */}
        <div className="space-y-3">
          <button
            onClick={() => handleExit('/')}
            className="w-full bg-slate-900 hover:bg-black text-white py-4 px-6 font-bold transition-all flex items-center justify-center rounded-none group"
          >
            <span>На головну</span>
            <Home className="w-4 h-4 ml-2 group-hover:scale-110 transition-transform" />
          </button>

          <button
            onClick={() => handleExit('/clothing')}
            className="w-full bg-white border border-slate-200 text-slate-600 hover:text-slate-900 hover:bg-slate-50 py-4 px-6 font-medium transition-all flex items-center justify-center rounded-none"
          >
            <span>Переглянути ще одяг</span>
            <ArrowRight className="w-4 h-4 ml-2" />
          </button>
        </div>

        <div className="mt-8 pt-8 border-t border-slate-100">
          <p className="text-xs text-slate-400 uppercase tracking-wide">
            Якщо у вас виникли питання, зв'яжіться з нами
          </p>
        </div>
      </div>
    </div>
  );
};
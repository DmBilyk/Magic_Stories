import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, Check, Clock, Phone, User } from 'lucide-react';
import { Header } from '../components/Header';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { bookingService } from '../services/api';

const ALL_INCLUSIVE_PACKAGES = [
  {
    id: 'standart',
    name: 'Standart',
    image: '/assets/all_inclusive/all_inclusive_standart.jpg',
    features: ['2 години оренди студії', 'Базовий реквізит', 'Підтримка адміністратора']
  },
  {
    id: 'family',
    name: 'Family',
    image: '/assets/all_inclusive/all_inclusive_family.jpg',
    features: ['3 години оренди студії', 'Розширений реквізит', 'Сімейні декорації', 'Допомога стиліста']
  },
  {
    id: 'gold',
    name: 'Gold',
    image: '/assets/all_inclusive/all_inclusive_gold.jpg',
    features: ['4 години оренди студії', 'Преміум реквізит', 'Професійний візаж', 'Зміна образів']
  },
  {
    id: 'premium',
    name: 'Premium',
    image: '/assets/all_inclusive/all_inclusive_premium.jpg',
    features: ['6 годин оренди студії', 'VIP декорації', 'Повний стиль-супровід', 'Фотограф в подарунок']
  }
];

const API_BASE = '/api';

export const AllInclusive = () => {
  const navigate = useNavigate();
  const [selectedPackage, setSelectedPackage] = useState<string | null>(null);
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const [formData, setFormData] = useState({
    firstName: '',
    lastName: '',
    phone: '+380'
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const selectedPkg = ALL_INCLUSIVE_PACKAGES.find(p => p.id === selectedPackage);

  const validatePhone = (phone: string): boolean => {
    const cleaned = phone.replace(/\D/g, '');
    return cleaned.length === 12 && cleaned.startsWith('380');
  };

  const handlePhoneChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    let value = e.target.value;
    if (!value.startsWith('+380')) {
      value = '+380';
    }
    if (value.length <= 13) {
      setFormData(prev => ({ ...prev, phone: value }));
      setErrors(prev => ({ ...prev, phone: '' }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.firstName.trim()) {
      newErrors.firstName = "Будь ласка, введіть ім'я";
    }
    if (!formData.lastName.trim()) {
      newErrors.lastName = 'Будь ласка, введіть прізвище';
    }
    if (!validatePhone(formData.phone)) {
      newErrors.phone = 'Невірний формат номера телефону';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) return;

    setLoading(true);
    try {

      await bookingService.createAllInclusiveRequest({
        packageType: selectedPackage,
        firstName: formData.firstName,
        lastName: formData.lastName,
        phoneNumber: formData.phone
      });

      setSubmitted(true);
    } catch (err) {
      console.error(err);
      alert('Помилка відправки заявки. Перевірте підключення або спробуйте ще раз.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white border border-slate-200 p-8 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 mb-4">Заявку прийнято!</h2>
          <p className="text-slate-600 mb-6">
            Ваша заявка на пакет <strong>{selectedPkg?.name}</strong> успішно відправлена.
            Адміністратор зв'яжеться з вами протягом наступної години.
          </p>
          <p className="text-sm text-slate-400 mb-6">
            <Clock className="w-4 h-4 inline mr-1" />
            Години роботи: 9:00 - 20:00
          </p>
          <button
            onClick={() => navigate('/')}
            className="w-full bg-slate-900 text-white py-3 hover:bg-black transition-colors"
          >
            На головну
          </button>
        </div>
      </div>
    );
  }

  if (step === 2) {
    return (
      <div className="min-h-screen bg-slate-50">
        <Header />

        <div className="bg-white border-b border-slate-200">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
            <button
              onClick={() => setStep(1)}
              className="flex items-center text-slate-500 hover:text-slate-900 transition-colors"
            >
              <ArrowLeft className="w-5 h-5 mr-2" />
              <span className="font-medium">Назад до пакетів</span>
            </button>
          </div>
        </div>

        <div className="max-w-2xl mx-auto px-4 py-12">
          <div className="bg-white border border-slate-200 p-8">
            <h1 className="text-3xl font-bold text-slate-900 mb-2">
              Замовлення пакету {selectedPkg?.name}
            </h1>
            <p className="text-slate-600 mb-8">
              Заповніть контактні дані, і наш адміністратор зв'яжеться з вами для уточнення деталей
            </p>

            <div className="bg-slate-50 p-6 mb-8 border border-slate-100">
              <h3 className="font-semibold mb-3">Що входить в пакет:</h3>
              <ul className="space-y-2">
                {selectedPkg?.features.map((feature, idx) => (
                  <li key={idx} className="flex items-start text-sm text-slate-600">
                    <Check className="w-4 h-4 mr-2 mt-0.5 text-green-600 flex-shrink-0" />
                    {feature}
                  </li>
                ))}
              </ul>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                  Ім'я
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    value={formData.firstName}
                    onChange={(e) => {
                      setFormData(prev => ({ ...prev, firstName: e.target.value }));
                      setErrors(prev => ({ ...prev, firstName: '' }));
                    }}
                    className={`w-full pl-12 pr-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none ${
                      errors.firstName ? 'border-red-400' : 'border-slate-200'
                    }`}
                    placeholder="Іван"
                  />
                </div>
                {errors.firstName && <p className="text-red-600 text-sm mt-2">{errors.firstName}</p>}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                  Прізвище
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="text"
                    value={formData.lastName}
                    onChange={(e) => {
                      setFormData(prev => ({ ...prev, lastName: e.target.value }));
                      setErrors(prev => ({ ...prev, lastName: '' }));
                    }}
                    className={`w-full pl-12 pr-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none ${
                      errors.lastName ? 'border-red-400' : 'border-slate-200'
                    }`}
                    placeholder="Петренко"
                  />
                </div>
                {errors.lastName && <p className="text-red-600 text-sm mt-2">{errors.lastName}</p>}
              </div>

              <div>
                <label className="block text-sm font-semibold text-slate-700 mb-2 uppercase tracking-wide text-xs">
                  Телефон
                </label>
                <div className="relative">
                  <Phone className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
                  <input
                    type="tel"
                    value={formData.phone}
                    onChange={handlePhoneChange}
                    className={`w-full pl-12 pr-5 py-4 border focus:outline-none focus:ring-1 focus:ring-slate-900 transition-all rounded-none tracking-wider font-medium ${
                      errors.phone ? 'border-red-400' : 'border-slate-200'
                    }`}
                    placeholder="+380XXXXXXXXX"
                    maxLength={13}
                  />
                </div>
                {errors.phone && <p className="text-red-600 text-sm mt-2">{errors.phone}</p>}
              </div>
            </div>

            <div className="mt-8 pt-6 border-t border-slate-100">
              <p className="text-xs text-slate-400 text-center mb-4">
                <Clock className="w-3 h-3 inline mr-1" />
                Години роботи: 9:00 - 20:00
              </p>
              <button
                onClick={handleSubmit}
                disabled={loading}
                className="w-full bg-slate-900 text-white py-4 font-bold hover:bg-black transition-colors disabled:opacity-50 flex items-center justify-center"
              >
                {loading ? <LoadingSpinner /> : 'Підтвердити замовлення'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white">
      <Header />

      <div className="bg-white border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <button
            onClick={() => navigate('/')}
            className="flex items-center text-slate-500 hover:text-slate-900 transition-colors"
          >
            <ArrowLeft className="w-5 h-5 mr-2" />
            <span className="font-medium">На головну</span>
          </button>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-20">
        <div className="text-center mb-16">
          <div className="inline-block border-b border-neutral-200 pb-2 mb-4">
            <h2 className="text-xs font-light tracking-[0.3em] uppercase text-neutral-400">
              ALL-INCLUSIVE
            </h2>
          </div>
          <h1 className="text-4xl font-light text-black mb-4 tracking-tight">
            Пакетні пропозиції
          </h1>
          <p className="text-neutral-500 font-light max-w-2xl mx-auto">
            Оберіть готовий пакет для вашої фотосесії. Все включено — просто оберіть та насолоджуйтесь!
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8">
          {ALL_INCLUSIVE_PACKAGES.map((pkg) => (
            <div
              key={pkg.id}
              className="group bg-white border border-neutral-200 hover:border-black transition-all duration-300 flex flex-col"
            >
            <div className="aspect-[9/16] overflow-hidden relative">
              <img
                src={pkg.image}
                alt={pkg.name}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
              />
            </div>
              <div className="p-6 flex flex-col flex-1">
                <h3 className="text-2xl font-light text-black mb-4">{pkg.name}</h3>

                <ul className="space-y-2 mb-6 flex-1">
                  {pkg.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start text-sm text-neutral-600">
                      <Check className="w-4 h-4 mr-2 mt-0.5 text-black flex-shrink-0" />
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  onClick={() => {
                    setSelectedPackage(pkg.id);
                    setStep(2);
                  }}
                  className="w-full bg-slate-900 text-white py-3 font-light text-sm uppercase tracking-wider hover:bg-black transition-colors"
                >
                  Обрати пакет
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
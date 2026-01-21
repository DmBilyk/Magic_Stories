import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ShoppingCart, Search, Plus, Minus, Shirt } from 'lucide-react';
import { useBooking } from '../context/BookingContext';
import { clothingService } from '../services/api';
// Імпортуємо наш новий компонент
import { OptimizedImage } from '../components/OptimizedImage';
import { LoadingSpinner } from '../components/LoadingSpinner';
import { ErrorMessage } from '../components/ErrorMessage';
import { ClothingRentalSkeleton } from '../components/Skeleton';
import type { ClothingCategory, ClothingItem } from '../types';
import { formatCurrency } from '../utils/dateTime';

export const ClothingRental = () => {
  const navigate = useNavigate();
  const {
    selectedLocation,
    bookingDate,
    bookingTime,
    durationHours,
    clothingCart,
    setClothingCart,
  } = useBooking();

  const [categories, setCategories] = useState<ClothingCategory[]>([]);
  const [items, setItems] = useState<ClothingItem[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    // Якщо користувач спробував зайти сюди без вибору дати - повертаємо назад
    if (!selectedLocation || !bookingDate || !bookingTime) {
      navigate('/booking');
      return;
    }
    loadData();
  }, [selectedLocation, bookingDate, bookingTime, navigate]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [categoriesData, itemsData] = await Promise.all([
        clothingService.getCategories(),
        clothingService.getItems({ availableOnly: true }),
      ]);
      setCategories(categoriesData.filter((c) => c.isActive));
      setItems(itemsData);
      setError('');
    } catch (err) {
      console.error(err);
      setError(err instanceof Error ? err.message : 'Failed to load clothing items');
    } finally {
      setLoading(false);
    }
  };

  // Фільтрація товарів (пошук + категорія)
  const filteredItems = items.filter((item) => {
    const matchesCategory = !selectedCategory || item.category?.id === selectedCategory;
    const query = searchQuery.toLowerCase().trim();
    const name = (item.name || '').toLowerCase();
    const description = (item.description || '').toLowerCase();

    const matchesSearch = !query || name.includes(query) || description.includes(query);

    return matchesCategory && matchesSearch;
  });

  const getItemQuantity = (itemId: string): number => {
    return clothingCart.find((cartItem) => cartItem.item.id === itemId)?.quantity || 0;
  };

  const addToCart = async (item: ClothingItem) => {
    if (!bookingDate || !bookingTime || !durationHours) {
      setError('Будь ласка, оберіть дату, час та тривалість перед додаванням до кошика');
      return;
    }

    const currentQuantity = getItemQuantity(item.id);
    const newQuantity = currentQuantity + 1;

    // Перевірка 1: Чи не перевищуємо загальну кількість цього товару
    if (newQuantity > item.quantity) {
      setError(`Доступно лише ${item.quantity} шт.`);
      return;
    }

    // Перевірка 2: Максимум 10 позицій (якщо це новий товар)
    if (clothingCart.length >= 10 && currentQuantity === 0) {
      setError('Максимум 10 різних речей на одне бронювання');
      return;
    }

    try {
      // Підготовка даних для перевірки на бекенді
      const formattedDate = bookingDate.includes('T') ? bookingDate.split('T')[0] : bookingDate;
      const formattedTime = bookingTime.includes(':') ? bookingTime.substring(0, 5) : bookingTime;

      // Запит на бекенд: чи вільна річ у цей час?
      const availabilityCheck = await clothingService.checkAvailability({
        itemId: item.id,
        bookingDate: formattedDate,
        bookingTime: formattedTime,
        durationHours: durationHours,
        quantity: newQuantity
      });

      if (!availabilityCheck.available) {
        setError(availabilityCheck.message);
        return;
      }

      // Якщо все ок - оновлюємо кошик
      setClothingCart((prev) => {
        const existing = prev.find((cartItem) => cartItem.item.id === item.id);
        if (existing) {
          return prev.map((cartItem) =>
            cartItem.item.id === item.id ? { ...cartItem, quantity: newQuantity } : cartItem
          );
        }
        return [...prev, { item, quantity: 1 }];
      });
      setError('');
    } catch (err) {
      console.error('Availability check failed:', err);
      setError(err instanceof Error ? err.message : 'Не вдалося перевірити доступність');
    }
  };

  const removeFromCart = (itemId: string) => {
    const currentQuantity = getItemQuantity(itemId);
    if (currentQuantity > 1) {
      setClothingCart((prev) =>
        prev.map((cartItem) =>
          cartItem.item.id === itemId ? { ...cartItem, quantity: currentQuantity - 1 } : cartItem
        )
      );
    } else {
      setClothingCart((prev) => prev.filter((cartItem) => cartItem.item.id !== itemId));
    }
    setError('');
  };

  const getTotalCost = (): number => {
    return clothingCart.reduce(
      (sum, cartItem) => sum + parseFloat(cartItem.item.price) * cartItem.quantity,
      0
    );
  };

  const handleContinue = () => {
    navigate('/summary');
  };

  if (loading) {
    // Якщо скелетон ще не імпортовано/створено, можна тимчасово: return <LoadingSpinner />
    return <ClothingRentalSkeleton />;
  }

  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-7xl mx-auto px-6 py-12">
        {/* Кнопка Назад */}
        <button
          onClick={() => navigate('/booking')}
          className="flex items-center text-black hover:text-neutral-600 mb-12 transition-colors group"
        >
          <ArrowLeft className="w-5 h-5 mr-2 group-hover:-translate-x-1 transition-transform" />
          <span className="text-sm tracking-wide">Назад до деталей бронювання</span>
        </button>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
          {/* ЛІВА ЧАСТИНА: Каталог */}
          <div className="lg:col-span-2">
            <div className="mb-16">
              <h1 className="text-5xl font-light text-black mb-3 tracking-tight">Оренда одягу</h1>
              <p className="text-neutral-500 text-lg font-light">Опціонально - Оберіть одяг для фотосесії</p>
            </div>

            {error && (
              <div className="mb-8">
                <ErrorMessage message={error} />
              </div>
            )}

            {/* Фільтри та Пошук */}
            <div className="mb-12">
              <div className="flex flex-col sm:flex-row gap-4 mb-8">
                <div className="flex-1 relative">
                  <Search className="absolute left-4 top-1/2 transform -translate-y-1/2 text-neutral-400 w-5 h-5" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder="Пошук одягу..."
                    className="w-full pl-12 pr-4 py-4 border border-neutral-200 bg-white focus:outline-none focus:border-neutral-400 transition-colors text-black placeholder-neutral-400"
                  />
                </div>
                <select
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  className="px-6 py-4 border border-neutral-200 bg-white focus:outline-none focus:border-neutral-400 transition-colors text-black"
                >
                  <option value="">Всі категорії</option>
                  {categories.map((category) => (
                    <option key={category.id} value={category.id}>
                      {category.name}
                    </option>
                  ))}
                </select>
              </div>

              {/* Сітка товарів */}
              {filteredItems.length === 0 ? (
                <div className="text-center py-24">
                  <Shirt className="w-16 h-16 text-neutral-200 mx-auto mb-4" />
                  <p className="text-neutral-400 font-light">Одяг не знайдено</p>
                </div>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                  {filteredItems.map((item) => {
                    const quantity = getItemQuantity(item.id);
                    // 🚀 ТУТ КЛЮЧОВА ЗМІНА: Вибираємо мініатюру, якщо є, інакше оригінал
                    const displayImage = item.primaryImage?.thumbnailUrl || item.primaryImage?.imageUrl;

                    return (
                      <div key={item.id} className="group flex flex-col h-full">
                        {/* Зображення */}
                        <div className="relative mb-4 border border-neutral-200 group-hover:border-amber-600 transition-colors">
                          {displayImage ? (
                            <OptimizedImage
                              src={displayImage}
                              alt={item.primaryImage?.altText || item.name}
                              aspectRatio="aspect-[3/4]"
                              className="w-full group-hover:scale-[1.02] transition-transform duration-500"
                            />
                          ) : (
                            <div className="aspect-[3/4] bg-neutral-50 flex items-center justify-center">
                              <Shirt className="w-12 h-12 text-neutral-300" />
                            </div>
                          )}

                          {/* Бейдж ціни */}
                          <div className="absolute top-4 right-4 bg-white border border-neutral-200 px-4 py-2 z-10 shadow-sm">
                            <span className="text-sm font-light text-black tracking-wider">
                              {formatCurrency(item.price)}
                            </span>
                          </div>
                        </div>

                        {/* Інфо про товар */}
                        <div className="space-y-3 flex-1">
                          <h3 className="font-light text-black text-lg tracking-wide">{item.name}</h3>
                          <p className="text-sm text-neutral-500 font-light line-clamp-2 min-h-[40px]">
                            {item.description}
                          </p>
                          <div className="flex items-center justify-between text-xs text-neutral-400 font-light tracking-wider uppercase">
                            <span>Розмір: {item.size}</span>
                            <span>Доступно: {item.quantity}</span>
                          </div>
                        </div>

                        {/* Кнопки додавання */}
                        <div className="mt-4">
                          {quantity > 0 ? (
                            <div className="flex items-center justify-between border border-neutral-200 p-2">
                              <button
                                onClick={() => removeFromCart(item.id)}
                                className="w-10 h-10 flex items-center justify-center hover:bg-neutral-50 transition-colors"
                              >
                                <Minus className="w-4 h-4 text-black" />
                              </button>
                              <span className="font-light text-black text-lg">{quantity}</span>
                              <button
                                onClick={() => addToCart(item)}
                                className="w-10 h-10 flex items-center justify-center hover:bg-neutral-50 transition-colors"
                              >
                                <Plus className="w-4 h-4 text-black" />
                              </button>
                            </div>
                          ) : (
                            <button
                              onClick={() => addToCart(item)}
                              className="w-full py-4 bg-black text-white font-light tracking-wider hover:bg-neutral-800 transition-colors text-sm uppercase"
                            >
                              Додати в кошик
                            </button>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* ПРАВА ЧАСТИНА: Кошик (Sticky) */}
          <div className="lg:col-span-1">
            <div className="border border-amber-600 p-8 sticky top-8 bg-white shadow-sm">
              <div className="flex items-center justify-between mb-8 pb-6 border-b border-neutral-200">
                <h2 className="text-2xl font-light text-black tracking-wide">Кошик</h2>
                <ShoppingCart className="w-6 h-6 text-black" />
              </div>

              {clothingCart.length === 0 ? (
                <div className="text-center py-12">
                  <p className="text-neutral-400 font-light mb-2">Кошик порожній</p>
                  <p className="text-xs text-neutral-400 font-light tracking-wide uppercase">Оренда одягу необов'язкова</p>
                </div>
              ) : (
                <div className="space-y-6 mb-8">
                  {clothingCart.map((cartItem) => (
                    <div key={cartItem.item.id} className="pb-6 border-b border-neutral-100 last:border-0">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex-1">
                          <h3 className="font-light text-black mb-1">{cartItem.item.name}</h3>
                          <p className="text-xs text-neutral-400 uppercase tracking-wider">Розмір: {cartItem.item.size}</p>
                        </div>
                        <button
                          onClick={() => removeFromCart(cartItem.item.id)}
                          className="text-neutral-400 hover:text-black text-xs uppercase tracking-wider transition-colors ml-4"
                        >
                          Видалити
                        </button>
                      </div>
                      <div className="flex justify-between items-center">
                        <span className="text-xs text-neutral-400 font-light">
                          {cartItem.quantity} шт × {formatCurrency(cartItem.item.price)}
                        </span>
                        <span className="font-light text-black">
                          {formatCurrency(parseFloat(cartItem.item.price) * cartItem.quantity)}
                        </span>
                      </div>
                    </div>
                  ))}

                  <div className="pt-6 border-t border-amber-600">
                    <div className="flex justify-between items-center">
                      <span className="text-sm font-light text-black uppercase tracking-wider">Разом</span>
                      <span className="text-2xl font-light text-black">
                        {formatCurrency(getTotalCost())}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                <button
                  onClick={handleContinue}
                  className="w-full py-4 bg-black text-white font-light tracking-wider hover:bg-neutral-800 transition-colors text-sm uppercase"
                >
                  Продовжити
                </button>

                <button
                  onClick={() => {
                    setClothingCart([]);
                    navigate('/summary');
                  }}
                  className="w-full py-4 border border-neutral-200 text-black hover:bg-neutral-50 transition-colors font-light tracking-wider text-sm uppercase"
                >
                  Пропустити оренду
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import type { Location, AdditionalService, CartClothingItem, CartPropItem } from '../types';

// Ключ, за яким ми будемо зберігати дані в браузері
const STORAGE_KEY = 'magic_stories_booking_state';

export interface ContactInfo {
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  notes: string;
}

interface BookingContextType {
  selectedLocation: Location | null;
  setSelectedLocation: (location: Location | null) => void;
  bookingDate: string;
  setBookingDate: (date: string) => void;
  bookingTime: string;
  setBookingTime: (time: string) => void;
  durationHours: number;
  setDurationHours: (hours: number) => void;
  selectedServices: AdditionalService[];
  setSelectedServices: (services: AdditionalService[]) => void;
  clothingCart: CartClothingItem[];
  setClothingCart: (items: CartClothingItem[]) => void;
  propsCart: CartPropItem[];
  setPropsCart: (items: CartPropItem[]) => void;
  contactInfo: ContactInfo;
  setContactInfo: (info: ContactInfo) => void;
  resetBooking: () => void;
}

const BookingContext = createContext<BookingContextType | undefined>(undefined);

export const BookingProvider = ({ children }: { children: ReactNode }) => {
  // 1. Функція для безпечного читання з localStorage
  const loadState = () => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      return saved ? JSON.parse(saved) : null;
    } catch (e) {
      console.error('Failed to load booking state', e);
      return null;
    }
  };

  const savedState = loadState();

  // 2. Ініціалізуємо стейти. Якщо є збережені дані — беремо їх, якщо ні — дефолтні.
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(
    savedState?.selectedLocation || null
  );
  const [bookingDate, setBookingDate] = useState<string>(
    savedState?.bookingDate || ''
  );
  const [bookingTime, setBookingTime] = useState<string>(
    savedState?.bookingTime || ''
  );
  const [durationHours, setDurationHours] = useState<number>(
    savedState?.durationHours || 2
  );
  const [selectedServices, setSelectedServices] = useState<AdditionalService[]>(
    savedState?.selectedServices || []
  );
  const [clothingCart, setClothingCart] = useState<CartClothingItem[]>(
    savedState?.clothingCart || []
  );
  const [propsCart, setPropsCart] = useState<CartPropItem[]>(
    savedState?.propsCart || []
  );

  const [contactInfo, setContactInfo] = useState<ContactInfo>(
    savedState?.contactInfo || {
      firstName: '',
      lastName: '',
      phone: '',
      email: '',
      notes: '',
    }
  );

  // 3. Ефект для автоматичного збереження при будь-якій зміні
  useEffect(() => {
    const stateToSave = {
      selectedLocation,
      bookingDate,
      bookingTime,
      durationHours,
      selectedServices,
      clothingCart,
      propsCart,
      contactInfo,
    };
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave));
  }, [
    selectedLocation,
    bookingDate,
    bookingTime,
    durationHours,
    selectedServices,
    clothingCart,
    propsCart,
    contactInfo,
  ]);

  const resetBooking = () => {
    // Скидаємо стейт
    setSelectedLocation(null);
    setBookingDate('');
    setBookingTime('');
    setDurationHours(2);
    setSelectedServices([]);
    setClothingCart([]);
    setPropsCart([]);
    setContactInfo({
      firstName: '',
      lastName: '',
      phone: '',
      email: '',
      notes: '',
    });
    // Очищаємо localStorage
    localStorage.removeItem(STORAGE_KEY);
  };

  return (
    <BookingContext.Provider
      value={{
        selectedLocation,
        setSelectedLocation,
        bookingDate,
        setBookingDate,
        bookingTime,
        setBookingTime,
        durationHours,
        setDurationHours,
        selectedServices,
        setSelectedServices,
        clothingCart,
        setClothingCart,
        propsCart,
        setPropsCart,
        contactInfo,
        setContactInfo,
        resetBooking,
      }}
    >
      {children}
    </BookingContext.Provider>
  );
};

export const useBooking = () => {
  const context = useContext(BookingContext);
  if (!context) {
    throw new Error('useBooking must be used within BookingProvider');
  }
  return context;
};
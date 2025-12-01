import { createContext, useContext, useState, ReactNode } from 'react';
import type { Location, AdditionalService, CartClothingItem, CartPropItem } from '../types';

// 1. Define the interface for contact info
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
  // New fields
  contactInfo: ContactInfo;
  setContactInfo: (info: ContactInfo) => void;
  resetBooking: () => void;
}

const BookingContext = createContext<BookingContextType | undefined>(undefined);

export const BookingProvider = ({ children }: { children: ReactNode }) => {
  const [selectedLocation, setSelectedLocation] = useState<Location | null>(null);
  const [bookingDate, setBookingDate] = useState('');
  const [bookingTime, setBookingTime] = useState('');
  const [durationHours, setDurationHours] = useState(2);
  const [selectedServices, setSelectedServices] = useState<AdditionalService[]>([]);
  const [clothingCart, setClothingCart] = useState<CartClothingItem[]>([]);
  const [propsCart, setPropsCart] = useState<CartPropItem[]>([]);

  // 2. Initialize contact info state
  const [contactInfo, setContactInfo] = useState<ContactInfo>({
    firstName: '',
    lastName: '',
    phone: '',
    email: '',
    notes: '',
  });

  const resetBooking = () => {
    setSelectedLocation(null);
    setBookingDate('');
    setBookingTime('');
    setDurationHours(2);
    setSelectedServices([]);
    setClothingCart([]);
    setPropsCart([]);
    // 3. Reset contact info
    setContactInfo({
      firstName: '',
      lastName: '',
      phone: '',
      email: '',
      notes: '',
    });
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
        contactInfo,     // Exposed
        setContactInfo,  // Exposed
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
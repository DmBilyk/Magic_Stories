export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const API_ENDPOINTS = {
  locations: `${API_BASE_URL}/locations/`,
  services: `${API_BASE_URL}/services/`,

  // FIXED: було /bookings/bookings/
  bookings: `${API_BASE_URL}/bookings/`,

  availability: `${API_BASE_URL}/bookings/availability/`,
  bookingSettings: `${API_BASE_URL}/bookings/settings/`,

  clothingCategories: `${API_BASE_URL}/clothing/categories/`,
  clothingItems: `${API_BASE_URL}/clothing/items/`,
  clothingAvailability: `${API_BASE_URL}/clothing/availability/`,
  clothingSettings: `${API_BASE_URL}/clothing/settings/`,

  propCategories: `${API_BASE_URL}/props/categories/`,
  propItems: `${API_BASE_URL}/props/items/`,
  propAvailability: `${API_BASE_URL}/props/availability/`,
  propSettings: `${API_BASE_URL}/props/settings/`,
};

export const fetchAPI = async <T>(url: string, options?: RequestInit): Promise<T> => {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({ error: 'Network error' }));
    throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
  }

  return response.json();
};

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api';

export const API_ENDPOINTS = {
  locations: `${API_BASE_URL}/locations/`,
  services: `${API_BASE_URL}/services/`,


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

  payments: `${API_BASE_URL}/payments/`,




};


// Допоміжна функція для оновлення токена
const refreshToken = async (): Promise<string | null> => {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
        // Якщо refresh-токену немає, користувач не авторизований
        return null;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/token/refresh/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ refresh: refreshToken }),
        });

        if (!response.ok) {
            // Якщо оновлення не вдалося (наприклад, refresh-токен прострочений),
            // кидаємо помилку, щоб користувач вийшов.
            throw new Error('Failed to refresh token');
        }

        const data = await response.json();
        // Зберігаємо новий access-токен
        localStorage.setItem('access_token', data.access);
        return data.access;
    } catch (e) {
        // Якщо помилка, видаляємо всі токени та перенаправляємо на вхід
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        // ТУТ ПОТРІБНА ЛОГІКА ПЕРЕНАПРАВЛЕННЯ НА СТОРІНКУ ВХОДУ
        console.error('Logout required', e);
        return null;
    }
};

export const fetchAPI = async <T>(url: string, options?: RequestInit): Promise<T> => {
    let accessToken = localStorage.getItem('access_token');

    // --- ПЕРША СПРОБА ЗАПИТУ ---
    let response = await makeRequest(url, accessToken, options);

    if (response.status === 401) {
        // --- 401: СПРОБА ОНОВЛЕННЯ ТОКЕНУ ---
        const newAccessToken = await refreshToken();

        if (newAccessToken) {
            // --- ПОВТОРНА СПРОБА ЗАПИТУ З НОВИМ ТОКЕНОМ ---
            response = await makeRequest(url, newAccessToken, options);
        } else {
            // Не вдалося оновити токен, повертаємо 401
            throw new Error('HTTP error! status: 401. Session expired.');
        }
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: 'Network error' }));
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
};

// Допоміжна функція для створення запиту
const makeRequest = (url: string, token: string | null, options?: RequestInit) => {
    const headers = {
        'Content-Type': 'application/json',
        ...options?.headers,
        ...(token && { 'Authorization': `Bearer ${token}` }),
    };

    return fetch(url, {
        ...options,
        headers: headers,
    });
};
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { BookingProvider } from './context/BookingContext';
import { Home } from './pages/Home';
import { BookingForm } from './pages/BookingForm';
import { ClothingRental } from './pages/ClothingRental';
import { BookingSummary } from './pages/BookingSummary';
import { PaymentSuccessPage } from './pages/PaymentSuccessPage';
import AdminBookingPanel from './pages/adminPage';
import AdminLogin from './pages/admin_login';
import { ScrollToTop } from './components/ScrollToTop';

// Компонент для захисту адмінських маршрутів
const ProtectedRoute = ({ children }: { children: JSX.Element }) => {
  const token = localStorage.getItem('access_token');

  if (!token) {
    // Якщо токена немає, перекидаємо на новий логін
    return <Navigate to="/manager/login" replace />;
  }

  return children;
};

function App() {
  return (
    <BookingProvider>
      <BrowserRouter>
        <ScrollToTop />
        <Routes>
          {/* Публічні маршрути */}
          <Route path="/" element={<Home />} />
          <Route path="/booking" element={<BookingForm />} />
          <Route path="/clothing" element={<ClothingRental />} />
          <Route path="/summary" element={<BookingSummary />} />
          <Route path="/payment/success" element={<PaymentSuccessPage />} />

          {/* === ЗМІНА ТУТ: Використовуємо /manager замість /admin === */}
          {/* Це дозволяє уникнути конфлікту з Django Admin в Nginx */}

          <Route path="/manager/login" element={<AdminLogin />} />

          <Route
            path="/manager/dashboard"
            element={
              <ProtectedRoute>
                <AdminBookingPanel />
              </ProtectedRoute>
            }
          />

          {/* Якщо хтось спробує зайти просто на /manager */}
          <Route path="/manager" element={<Navigate to="/manager/dashboard" replace />} />

          {/* Старий шлях /admin залишаємо для Django (якщо він вам ще треба) */}
          {/* Або можна перенаправляти: */}
          {/* <Route path="/admin" element={<Navigate to="/manager/dashboard" replace />} /> */}
        </Routes>
      </BrowserRouter>
    </BookingProvider>
  );
}

export default App;
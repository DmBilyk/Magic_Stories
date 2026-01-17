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



          <Route path="/manager/login" element={<AdminLogin />} />

          <Route
            path="/manager/dashboard"
            element={
              <ProtectedRoute>
                <AdminBookingPanel />
              </ProtectedRoute>
            }
          />


          <Route path="/manager" element={<Navigate to="/manager/dashboard" replace />} />


        </Routes>
      </BrowserRouter>
    </BookingProvider>
  );
}

export default App;
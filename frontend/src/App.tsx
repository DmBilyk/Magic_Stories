import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { BookingProvider } from './context/BookingContext';
import { Home } from './pages/Home';
import { BookingForm } from './pages/BookingForm';
import { ClothingRental } from './pages/ClothingRental';
import { BookingSummary } from './pages/BookingSummary';

function App() {
  return (
    <BookingProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/booking" element={<BookingForm />} />
          <Route path="/clothing" element={<ClothingRental />} />
          <Route path="/summary" element={<BookingSummary />} />
        </Routes>
      </BrowserRouter>
    </BookingProvider>
  );
}

export default App;

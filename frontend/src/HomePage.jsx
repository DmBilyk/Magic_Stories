import { useState, useEffect } from 'react'
import api from '../services/api'

function HomePage() {
  const [message, setMessage] = useState('Завантаження...')

  useEffect(() => {
    // Приклад виклику API
    // api.get('/endpoint/').then(res => setMessage(res.data))
    setMessage('Вітаємо в Django + React додатку!')
  }, [])

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>{message}</h1>
      <p>Почніть розробку, редагуючи src/App.jsx</p>
    </div>
  )
}

export default HomePage
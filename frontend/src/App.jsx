import { useState, useEffect } from 'react'
import reactLogo from './assets/react.svg'
import viteLogo from './assets/vite.svg'
import heroImg from './assets/hero.png'
import './App.css'
import api from './api.js'

function App() {
  const [data, setData] = useState([]);
  const [status, setStatus] = useState('loading data...');

  useEffect(() => {
    api.get('/api/v1/sites').then((res) => {
      setData(res.data);
      setStatus('data loaded from backed successfully!');
    })
    .catch((err) => {
      console.error(err);
      setStatus('error loading data from backend check cors policy and backend server');
    });
  }, []);

  return (
    <div style={{ padding: '40px', fontFamily: 'Arial' }}>
      <h1>CUCM Dashboard</h1>
      <div style={{ 
        padding: '10px', 
        backgroundColor: status.includes('שגיאה') ? '#ffcccc' : '#ccffcc',
        borderRadius: '5px'
      }}>
        {status}
      </div>

      <h2>נתונים מה-API:</h2>
      {data.length > 0 ? (
        <ul>
          {data.map((item, index) => (
            <li key={index}>{JSON.stringify(item.name || item)}</li>
          ))}
        </ul>
      ) : (
        <p>אין נתונים להצגה כרגע.</p>
      )}
    </div>
  )
}

export default App

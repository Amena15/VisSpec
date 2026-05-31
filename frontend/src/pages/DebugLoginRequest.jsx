import React, { useState } from 'react';
import { authAPI } from '../services/api';

const DebugLoginRequest = () => {
  const [email, setEmail] = useState('yousef@vispec.com');
  const [password, setPassword] = useState('Yousef@2026');
  const [result, setResult] = useState('');
  const [loading, setLoading] = useState(false);

  const onRun = async () => {
    setLoading(true);
    setResult('');
    try {
      const res = await authAPI.login({ username: email, password });
      setResult(JSON.stringify(res.data, null, 2));
    } catch (e) {
      setResult(
        JSON.stringify(
          {
            status: e?.response?.status,
            data: e?.response?.data,
          },
          null,
          2
        )
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: 16, fontFamily: 'sans-serif' }}>
      <h2>Debug Login Request</h2>
      <div style={{ display: 'grid', gap: 8, maxWidth: 480 }}>
        <label>
          Email
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%' }} />
        </label>
        <label>
          Password
          <input value={password} type="password" onChange={(e) => setPassword(e.target.value)} style={{ width: '100%' }} />
        </label>
        <button onClick={onRun} disabled={loading}>
          {loading ? 'Running...' : 'Run authAPI.login()'}
        </button>
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{result}</pre>
      </div>
    </div>
  );
};

export default DebugLoginRequest;


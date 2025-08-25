/* Biasware LLC Proprietary */
import Head from 'next/head';
import React, { useState } from 'react';
import { searchVideos, VideoResult } from '../lib/api';

const Home: React.FC = () => {
  const [q, setQ] = useState('attack lineout');
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<VideoResult[]>([]);
  const [error, setError] = useState<string | null>(null);

  async function doSearch(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const data = await searchVideos(q, 5);
      setResults(data);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Head>
        <title>Rugby Frontend</title>
        <meta name="viewport" content="initial-scale=1.0, width=device-width" />
      </Head>
      <main style={{padding: '2rem', fontFamily: 'sans-serif', maxWidth: 900, margin: '0 auto'}}>
        <h1>Rugby Frontend</h1>
        <p>Semantic search over indexed rugby videos.</p>
        <form onSubmit={doSearch} style={{marginBottom: '1rem'}}>
          <input
            value={q}
            onChange={(e) => setQ(e.target.value)}
            placeholder="Search videos..."
            style={{padding: '0.5rem', width: '60%'}}
          />{' '}
          <button type="submit" disabled={loading} style={{padding: '0.55rem 1rem'}}>
            {loading ? 'Searching...' : 'Search'}
          </button>
        </form>
        {error && <p style={{color: 'red'}}>{error}</p>}
        <ul style={{listStyle: 'none', padding: 0}}>
          {results.map((r, i) => (
            <li key={i} style={{marginBottom: '1rem', background: '#f6f6f6', padding: '1rem', borderRadius: 6}}>
              <strong>Path:</strong> {r.path}<br />
              <strong>Summary:</strong> {r.summary}
            </li>
          ))}
        </ul>
      </main>
    </>
  );
};

export default Home;

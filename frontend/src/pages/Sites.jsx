import {useEffect, useState} from 'react'
import api from '../api.js';

const Sites = () => {
    const [sites, setSites] = useState([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        api.get('/api/v1/sites').then(res => {
            setSites(res.data);
            setLoading(false);
        })
        .catch(err => {
            console.error('Failed to fetch sites:', err);
            setLoading(false);
        });
    }, []);

    if (loading) return <p className="flex justify-center p-10 text-gray-500">Loading sites...</p>;
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">Site Management</h1>
        <button className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors">
          + Add New Site
        </button>
      </div>

      <div className="bg-white rounded-2xl shadow-sm border border-gray-200 overflow-hidden">
        <table className="w-full text-left border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-200">
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">Site Name</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">Description</th>
              <th className="px-6 py-4 text-xs font-semibold text-gray-600 uppercase tracking-wider">Group ID</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {sites.map(site => (
              <tr key={site.id} className="hover:bg-gray-50 transition-colors cursor-pointer">
                <td className="px-6 py-4 text-sm font-medium text-gray-900">{site.name}</td>
                <td className="px-6 py-4 text-sm text-gray-500">{site.description || '—'}</td>
                <td className="px-6 py-4 text-sm font-mono text-indigo-600">{site.group_id}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

const tableHeaderStyle = { padding: '12px', borderBottom: '2px solid #ddd' };
const tableCellStyle = { padding: '12px' };

export default Sites

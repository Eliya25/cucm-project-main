import {useEffect, useState} from 'react'
import api from '../api.js';

const Sites = () => {
    const [sites, setSites] = useState([]);
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [newSite, setNewSite] = useState({ name: '', description: '', group_id: '' });
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

    const handleAddSite = async (e) => {
        e.preventDefault();
        try {
            const res = await api.post('/api/v1/sites/', newSite);
            setSites([...sites, res.data]);
            setIsModalOpen(false);
            setNewSite({ name: '', description: '', group_id: '' });
        } catch (error) {
            console.error('Failed to add site:', error);
            alert('Failed to add site. Please try again.');
        }
    }

    if (loading) return <p className="flex justify-center p-10 text-gray-500 font-medium">Loading sites...</p>;
    
  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Site Management</h1>
        <button 
          onClick={() => setIsModalOpen(true)}
          className="bg-indigo-600 text-white px-5 py-2.5 rounded-xl font-medium hover:bg-indigo-700 shadow-sm transition-all flex items-center gap-2"
        >
          <span>+</span> Add New Site
        </button>
      </div>

      {/* הטבלה שסידרנו קודם... */}

      {/* Modal להוספת אתר */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 border border-gray-100">
            <h2 className="text-xl font-bold text-gray-900 mb-6">Create New Site</h2>
            <form onSubmit={handleAddSite} className="space-y-4">
              <input
                placeholder="Site Name"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                value={newSite.name}
                onChange={(e) => setNewSite({...newSite, name: e.target.value})}
                required
              />
              <textarea
                placeholder="Description"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none h-24"
                value={newSite.description}
                onChange={(e) => setNewSite({...newSite, description: e.target.value})}
              />
              <input
                placeholder="Group ID"
                className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-indigo-500 outline-none"
                value={newSite.group_id}
                onChange={(e) => setNewSite({...newSite, group_id: e.target.value})}
                required
              />
              <div className="flex gap-3 pt-4">
                <button 
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="flex-1 px-4 py-3 text-gray-600 font-medium hover:bg-gray-50 rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button 
                  type="submit"
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white font-medium rounded-xl hover:bg-indigo-700 transition-colors"
                >
                  Save Site
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
export default Sites

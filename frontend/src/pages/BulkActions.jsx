import { Zap } from 'lucide-react';

const BulkActions = () => {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Bulk Actions</h1>
        <p className="text-sm text-gray-500 mt-1">Perform actions on multiple items at once</p>
      </div>

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-16 text-center">
        <div className="inline-flex items-center justify-center w-16 h-16 bg-indigo-50 rounded-2xl mb-4">
          <Zap size={32} className="text-indigo-400" />
        </div>
        <h2 className="text-lg font-semibold text-gray-700 mb-2">Coming Soon</h2>
        <p className="text-gray-400 text-sm max-w-sm mx-auto">
          Bulk actions will allow you to manage multiple sites, sections, devices and users at once.
        </p>
      </div>
    </div>
  );
};

export default BulkActions;
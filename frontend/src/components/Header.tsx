import React from 'react';
import { Download, Info } from 'lucide-react';

interface HeaderProps {
  onExportCalendar?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  onExportCalendar,
}) => {
  const [showInfo, setShowInfo] = React.useState(false);

  return (
    <header
      className="bg-gradient-to-r from-gator-dark via-gator-light to-gator-accent shadow-gator"
      style={{
        backgroundImage: 'linear-gradient(90deg, #003DA5 0%, #0066FF 55%, #FF8200 100%)',
      }}
    >
      <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 bg-white rounded-lg flex items-center justify-center">
            <span className="text-2xl">🐊</span>
          </div>
          <div>
            <h1 className="text-3xl font-bold text-white">ScheduGator</h1>
            <p className="text-sm text-gator-gray-200">AI-Driven Academic Schedule Optimizer</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => setShowInfo(!showInfo)}
            className="flex items-center gap-2 px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition-all font-semibold"
            title="About ScheduGator"
          >
            <Info size={20} />
            About
          </button>
          <button
            onClick={onExportCalendar}
            className="flex items-center gap-2 px-4 py-2 bg-gator-accent hover:bg-orange-600 text-white rounded-lg transition-all font-semibold shadow-md"
          >
            <Download size={20} />
            Export Calendar
          </button>
        </div>
      </div>

      {/* Info Panel */}
      {showInfo && (
        <div className="bg-gator-dark bg-opacity-95 border-t-2 border-gator-accent px-6 py-4">
          <div className="max-w-7xl mx-auto grid md:grid-cols-3 gap-6">
            <div className="text-white">
              <h3 className="font-bold text-gator-accent mb-2">🤖 AI Advisor</h3>
              <p className="text-sm text-gator-gray-200">
                Describe your preferences and get conflict-free schedules instantly.
              </p>
            </div>
            <div className="text-white">
              <h3 className="font-bold text-gator-accent mb-2">📅 Smart Calendar</h3>
              <p className="text-sm text-gator-gray-200">
                Visualize your schedule at a glance with automatic conflict detection.
              </p>
            </div>
            <div className="text-white">
              <h3 className="font-bold text-gator-accent mb-2">✅ Verification</h3>
              <p className="text-sm text-gator-gray-200">
                Automatic prerequisite and critical tracking validation.
              </p>
            </div>
          </div>
        </div>
      )}
    </header>
  );
};

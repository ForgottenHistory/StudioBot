import { useState, useEffect } from 'react';
import {
  Circle,
  Server,
  Cpu,
  Users,
  Calendar,
  Play,
  Square,
  RefreshCw
} from 'lucide-react';

const ServerStatus = ({
  serverStatus,
  controlScheduler,
  getSchedulerStatus,
  checkServerStatus
}) => {
  const [schedulerStatus, setSchedulerStatus] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const loadSchedulerStatus = async () => {
    const result = await getSchedulerStatus();
    if (result.success) {
      setSchedulerStatus(result.data);
    }
  };

  useEffect(() => {
    if (serverStatus.running) {
      loadSchedulerStatus();
      const interval = setInterval(loadSchedulerStatus, 5000);
      return () => clearInterval(interval);
    }
  }, [serverStatus.running]);

  const handleSchedulerAction = async (action) => {
    setIsLoading(true);
    await controlScheduler(action);
    await loadSchedulerStatus();
    setIsLoading(false);
  };

  const handleRefresh = async () => {
    setIsLoading(true);
    await checkServerStatus();
    await loadSchedulerStatus();
    setIsLoading(false);
  };

  return (
    <div className="space-y-6">
      {/* Server Status Card */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
            <Server className="h-5 w-5" />
            Server Status
          </h2>
          <button
            onClick={handleRefresh}
            disabled={isLoading}
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        <div className="flex items-center gap-3 mb-4">
          <Circle
            className={`h-3 w-3 ${
              serverStatus.running ? 'text-green-500 fill-current' : 'text-red-500 fill-current'
            }`}
          />
          <span className={`font-medium ${
            serverStatus.running ? 'text-green-700' : 'text-red-700'
          }`}>
            {serverStatus.running ? 'Running' : 'Not Connected'}
          </span>
        </div>

        {serverStatus.running && serverStatus.data && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Cpu className="h-4 w-4" />
                <span className="text-sm">Device</span>
              </div>
              <span className="font-semibold text-gray-900">
                {serverStatus.data.tts_device?.toUpperCase()}
              </span>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Calendar className="h-4 w-4" />
                <span className="text-sm">Topics</span>
              </div>
              <span className="font-semibold text-gray-900">
                {serverStatus.data.topics_loaded}
              </span>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Users className="h-4 w-4" />
                <span className="text-sm">Personalities</span>
              </div>
              <span className="font-semibold text-gray-900">
                {serverStatus.data.personalities_loaded}
              </span>
            </div>

            <div className="bg-gray-50 rounded-lg p-3">
              <div className="flex items-center gap-2 text-gray-600 mb-1">
                <Server className="h-4 w-4" />
                <span className="text-sm">OpenRouter</span>
              </div>
              <span className={`font-semibold ${
                serverStatus.data.openrouter_available ? 'text-green-600' : 'text-red-600'
              }`}>
                {serverStatus.data.openrouter_available ? 'Available' : 'Unavailable'}
              </span>
            </div>
          </div>
        )}

        {serverStatus.error && (
          <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-red-700 text-sm">{serverStatus.error}</p>
          </div>
        )}
      </div>

      {/* Scheduler Controls */}
      {serverStatus.running && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Scheduler Control</h3>

          {schedulerStatus && (
            <div className="mb-4">
              <div className="flex items-center gap-3 mb-3">
                <Circle
                  className={`h-3 w-3 ${
                    schedulerStatus.running ? 'text-green-500 fill-current' : 'text-gray-400 fill-current'
                  }`}
                />
                <span className={`font-medium ${
                  schedulerStatus.running ? 'text-green-700' : 'text-gray-700'
                }`}>
                  {schedulerStatus.running ? 'Scheduler Running' : 'Scheduler Stopped'}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm text-gray-600">
                <div>
                  <span className="font-medium">Ad Interval:</span> {schedulerStatus.ad_interval}s
                </div>
                <div>
                  <span className="font-medium">Conversation Interval:</span> {schedulerStatus.conversation_interval}s
                </div>
              </div>
            </div>
          )}

          <div className="flex gap-3">
            <button
              onClick={() => handleSchedulerAction('start')}
              disabled={isLoading || (schedulerStatus?.running)}
              className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Play className="h-4 w-4" />
              Start Scheduler
            </button>

            <button
              onClick={() => handleSchedulerAction('stop')}
              disabled={isLoading || (!schedulerStatus?.running)}
              className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <Square className="h-4 w-4" />
              Stop Scheduler
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default ServerStatus;
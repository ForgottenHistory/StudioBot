import { useState } from 'react';
import { Radio, Settings, Eye, Zap } from 'lucide-react';

import { useRadioServer } from './hooks/useRadioServer';
import ServerStatus from './components/ServerStatus';
import ContentGenerator from './components/ContentGenerator';
import ContentViewer from './components/ContentViewer';

function App() {
  const [activeTab, setActiveTab] = useState('status');

  const {
    serverStatus,
    topics,
    personalities,
    generatedContent,
    checkServerStatus,
    loadGeneratedContent,
    generateAd,
    generateConversation,
    generateConversationWithAudio,
    controlScheduler,
    getSchedulerStatus,
    playAudio,
    BASE_URL
  } = useRadioServer();

  const tabs = [
    {
      id: 'status',
      label: 'Server Status',
      icon: Settings,
      component: ServerStatus
    },
    {
      id: 'generate',
      label: 'Generate Content',
      icon: Zap,
      component: ContentGenerator
    },
    {
      id: 'content',
      label: 'Browse Content',
      icon: Eye,
      component: ContentViewer
    }
  ];

  const renderActiveComponent = () => {
    const activeTabData = tabs.find(tab => tab.id === activeTab);
    if (!activeTabData) return null;

    const Component = activeTabData.component;

    switch (activeTab) {
      case 'status':
        return (
          <Component
            serverStatus={serverStatus}
            controlScheduler={controlScheduler}
            getSchedulerStatus={getSchedulerStatus}
            checkServerStatus={checkServerStatus}
          />
        );

      case 'generate':
        return (
          <Component
            topics={topics}
            personalities={personalities}
            generateAd={generateAd}
            generateConversation={generateConversation}
            generateConversationWithAudio={generateConversationWithAudio}
            playAudio={playAudio}
          />
        );

      case 'content':
        return (
          <Component
            topics={topics}
            personalities={personalities}
            generatedContent={generatedContent}
            loadGeneratedContent={loadGeneratedContent}
            BASE_URL={BASE_URL}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-blue-600 rounded-lg">
                <Radio className="h-6 w-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Enhanced Radio Server</h1>
                <p className="text-sm text-gray-600">AI-Powered Content Generation System</p>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <div className={`h-2 w-2 rounded-full ${
                serverStatus.running ? 'bg-green-500' : 'bg-red-500'
              }`}></div>
              <span className={`text-sm font-medium ${
                serverStatus.running ? 'text-green-700' : 'text-red-700'
              }`}>
                {serverStatus.running ? 'Connected' : 'Disconnected'}
              </span>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <nav className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex space-x-8">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {!serverStatus.running && activeTab !== 'status' && (
          <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <div className="flex">
              <div className="flex-shrink-0">
                <Settings className="h-5 w-5 text-yellow-400" />
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">
                  Server Not Connected
                </h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>
                    The radio server is not running or not accessible.
                    Please check the{' '}
                    <button
                      onClick={() => setActiveTab('status')}
                      className="underline hover:text-yellow-900"
                    >
                      Server Status
                    </button>
                    {' '}tab for more information.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}

        {renderActiveComponent()}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="flex justify-between items-center">
            <div className="text-sm text-gray-500">
              Enhanced Radio Server Control Panel
            </div>
            <div className="text-sm text-gray-500">
              API: <code className="bg-gray-100 px-1 rounded">{BASE_URL}</code>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
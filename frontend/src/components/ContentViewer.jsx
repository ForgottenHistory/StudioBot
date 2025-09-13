import { useState, useEffect } from 'react';
import {
  Users,
  Calendar,
  FileText,
  ExternalLink,
  Mic,
  RefreshCw
} from 'lucide-react';

const ContentViewer = ({
  topics,
  personalities,
  generatedContent,
  loadGeneratedContent,
  BASE_URL
}) => {
  const [selectedTab, setSelectedTab] = useState('topics');
  const [selectedContent, setSelectedContent] = useState(null);
  const [isLoading, setIsLoading] = useState(false);

  const handleRefreshContent = async () => {
    setIsLoading(true);
    await loadGeneratedContent();
    setIsLoading(false);
  };

  const viewGeneratedFile = async (filename) => {
    try {
      // Since we can't directly read files from the frontend,
      // we'll show the file info and provide a link to download
      setSelectedContent({
        filename,
        note: "Click the external link to download and view this file."
      });
    } catch (error) {
      console.error('Error viewing file:', error);
    }
  };

  const tabs = [
    { id: 'topics', label: 'Topics', icon: Calendar },
    { id: 'personalities', label: 'Personalities', icon: Users },
    { id: 'generated', label: 'Generated Content', icon: FileText }
  ];

  return (
    <div className="space-y-6">
      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-md">
        <div className="border-b border-gray-200">
          <nav className="flex space-x-8 px-6">
            {tabs.map(tab => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setSelectedTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 transition-colors ${
                    selectedTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {tab.label}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="p-6">
          {/* Topics Tab */}
          {selectedTab === 'topics' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Available Topics</h3>
              {Object.keys(topics).length === 0 ? (
                <p className="text-gray-500">No topics loaded.</p>
              ) : (
                <div className="grid gap-4">
                  {Object.entries(topics).map(([key, topic]) => (
                    <div key={key} className="border border-gray-200 rounded-lg p-4">
                      <h4 className="font-semibold text-gray-900 mb-2">{topic.theme}</h4>
                      <p className="text-gray-600 mb-3">{topic.description}</p>
                      <div className="flex items-center gap-4 text-sm text-gray-500">
                        <span>Keywords: {topic.keywords?.length || 0}</span>
                        <span>Products: {topic.product_count}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Personalities Tab */}
          {selectedTab === 'personalities' && (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Radio Personalities</h3>
              {Object.keys(personalities).length === 0 ? (
                <p className="text-gray-500">No personalities loaded.</p>
              ) : (
                <div className="grid gap-4">
                  {Object.entries(personalities).map(([key, personality]) => (
                    <div key={key} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between mb-2">
                        <h4 className="font-semibold text-gray-900">{personality.name}</h4>
                        <span className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full">
                          {personality.role}
                        </span>
                      </div>
                      <p className="text-gray-600 mb-3">{personality.description}</p>
                      <div className="space-y-2 text-sm">
                        <div className="flex items-center gap-2">
                          <Mic className="h-4 w-4 text-gray-400" />
                          <span className="text-gray-600">Voice: {personality.voice}</span>
                        </div>
                        <div className="text-gray-600">
                          <span className="font-medium">Speaking Style:</span> {personality.speaking_style}
                        </div>
                        <div className="text-gray-600">
                          <span className="font-medium">Catchphrases:</span> {personality.catchphrases_count} loaded
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Generated Content Tab */}
          {selectedTab === 'generated' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold text-gray-900">Generated Content History</h3>
                <button
                  onClick={handleRefreshContent}
                  disabled={isLoading}
                  className="flex items-center gap-2 px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
                >
                  <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
                  Refresh
                </button>
              </div>

              {generatedContent.length === 0 ? (
                <p className="text-gray-500">No generated content found.</p>
              ) : (
                <div className="space-y-2">
                  {generatedContent.map((item, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                    >
                      <div className="flex-1">
                        <div className="font-medium text-gray-900">{item.filename}</div>
                        <div className="text-sm text-gray-500">
                          {item.size} bytes • Modified: {new Date(item.modified).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={() => viewGeneratedFile(item.filename)}
                          className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                          title="View File Info"
                        >
                          <FileText className="h-4 w-4" />
                        </button>
                        <a
                          href={`${BASE_URL}/generated_content/${item.filename}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                          title="Download File"
                        >
                          <ExternalLink className="h-4 w-4" />
                        </a>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* File Viewer Modal */}
      {selectedContent && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-2xl w-full max-h-96 overflow-hidden">
            <div className="p-4 border-b border-gray-200 flex items-center justify-between">
              <h4 className="text-lg font-semibold text-gray-900">{selectedContent.filename}</h4>
              <button
                onClick={() => setSelectedContent(null)}
                className="text-gray-400 hover:text-gray-600"
              >
                ×
              </button>
            </div>
            <div className="p-4">
              <p className="text-gray-600 mb-4">{selectedContent.note}</p>
              <div className="flex gap-2">
                <a
                  href={`${BASE_URL}/generated_content/${selectedContent.filename}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  Download File
                </a>
                <button
                  onClick={() => setSelectedContent(null)}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ContentViewer;
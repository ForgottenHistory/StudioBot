import { useState } from 'react';
import {
  Radio,
  MessageSquare,
  Play,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

const ContentGenerator = ({
  topics,
  personalities,
  generateAd,
  generateConversation,
  generateConversationWithAudio,
  playAudio
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState([]);

  // Ad generation state
  const [adParams, setAdParams] = useState({
    topic: '',
    personality: ''
  });

  // Conversation generation state
  const [convParams, setConvParams] = useState({
    host: '',
    guest: '',
    topic: ''
  });

  const handleGenerateAd = async () => {
    setIsGenerating(true);
    const result = await generateAd(adParams);

    const newResult = {
      id: Date.now(),
      type: 'ad',
      timestamp: new Date().toLocaleTimeString(),
      params: { ...adParams },
      ...result
    };

    setResults(prev => [newResult, ...prev]);
    setIsGenerating(false);

    // Reset form
    setAdParams({ topic: '', personality: '' });
  };

  const handleGenerateConversation = async () => {
    setIsGenerating(true);
    const result = await generateConversation(convParams);

    const newResult = {
      id: Date.now(),
      type: 'conversation',
      timestamp: new Date().toLocaleTimeString(),
      params: { ...convParams },
      ...result
    };

    setResults(prev => [newResult, ...prev]);
    setIsGenerating(false);

    // Reset form
    setConvParams({ host: '', guest: '', topic: '' });
  };

  const handleGenerateConversationWithAudio = async () => {
    setIsGenerating(true);
    const result = await generateConversationWithAudio(convParams);

    const newResult = {
      id: Date.now(),
      type: 'conversation_with_audio',
      timestamp: new Date().toLocaleTimeString(),
      params: { ...convParams },
      ...result
    };

    setResults(prev => [newResult, ...prev]);
    setIsGenerating(false);

    // Reset form
    setConvParams({ host: '', guest: '', topic: '' });
  };

  const handlePlayAudio = (audioUrl) => {
    if (audioUrl) {
      playAudio(audioUrl);
    }
  };

  const topicOptions = Object.keys(topics);
  const personalityOptions = Object.values(personalities).map(p => p.name);

  return (
    <div className="space-y-6">
      {/* Ad Generation */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <Radio className="h-5 w-5" />
          Generate Advertisement
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic (optional)
            </label>
            <select
              value={adParams.topic}
              onChange={(e) => setAdParams(prev => ({ ...prev, topic: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Random Topic</option>
              {topicOptions.map(topic => (
                <option key={topic} value={topic}>
                  {topics[topic]?.theme || topic}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Personality (optional)
            </label>
            <select
              value={adParams.personality}
              onChange={(e) => setAdParams(prev => ({ ...prev, personality: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Random Personality</option>
              {personalityOptions.map(name => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end">
            <button
              onClick={handleGenerateAd}
              disabled={isGenerating}
              className="w-full px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Radio className="h-4 w-4" />
                  Generate Ad
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Conversation Generation */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <MessageSquare className="h-5 w-5" />
          Generate Conversation
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Host (optional)
            </label>
            <select
              value={convParams.host}
              onChange={(e) => setConvParams(prev => ({ ...prev, host: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Auto Select Host</option>
              {personalityOptions.map(name => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Guest (optional)
            </label>
            <select
              value={convParams.guest}
              onChange={(e) => setConvParams(prev => ({ ...prev, guest: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Auto Select Guest</option>
              {personalityOptions.map(name => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic (optional)
            </label>
            <select
              value={convParams.topic}
              onChange={(e) => setConvParams(prev => ({ ...prev, topic: e.target.value }))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
            >
              <option value="">Random Topic</option>
              {topicOptions.map(topic => (
                <option key={topic} value={topic}>
                  {topics[topic]?.theme || topic}
                </option>
              ))}
            </select>
          </div>

          <div className="flex items-end gap-2">
            <button
              onClick={handleGenerateConversation}
              disabled={isGenerating}
              className="flex-1 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <MessageSquare className="h-4 w-4" />
                  Generate Text
                </>
              )}
            </button>
            <button
              onClick={handleGenerateConversationWithAudio}
              disabled={isGenerating}
              className="flex-1 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
            >
              {isGenerating ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Generating...
                </>
              ) : (
                <>
                  <Play className="h-4 w-4" />
                  Generate with Audio
                </>
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generation Results</h3>

        {results.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No content generated yet. Use the forms above to generate ads or conversations.
          </p>
        ) : (
          <div className="space-y-4 max-h-96 overflow-y-auto">
            {results.map(result => (
              <div
                key={result.id}
                className={`border rounded-lg p-4 ${
                  result.success ? 'border-green-200 bg-green-50' : 'border-red-200 bg-red-50'
                }`}
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {result.success ? (
                      <CheckCircle className="h-5 w-5 text-green-600" />
                    ) : (
                      <AlertCircle className="h-5 w-5 text-red-600" />
                    )}
                    <span className="font-medium text-gray-900">
                      {result.type === 'ad' ? 'Advertisement' :
                       result.type === 'conversation_with_audio' ? 'Conversation with Audio' : 'Conversation'} - {result.timestamp}
                    </span>
                  </div>

                  {result.success && result.data?.audio_url && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePlayAudio(result.data.audio_url)}
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                        title={result.type === 'conversation_with_audio' ? 'Play Complete Conversation' : 'Play Audio'}
                      >
                        <Play className="h-4 w-4" />
                      </button>
                      <a
                        href={`http://localhost:5000${result.data.audio_url}`}
                        download
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                        title={result.type === 'conversation_with_audio' ? 'Download Complete Conversation' : 'Download Audio'}
                      >
                        <Download className="h-4 w-4" />
                      </a>
                    </div>
                  )}
                </div>

                {result.success ? (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                      {result.type === 'ad' && (
                        <>
                          <span>Topic: {result.data.topic || 'Random'}</span>
                          <span>•</span>
                          <span>Personality: {result.data.personality}</span>
                        </>
                      )}
                      {result.type === 'conversation' && (
                        <>
                          <span>Host: {result.data.host}</span>
                          <span>•</span>
                          <span>Guest: {result.data.guest}</span>
                          <span>•</span>
                          <span>Topic: {result.data.topic}</span>
                        </>
                      )}
                    </div>
                    <div className="bg-white p-3 rounded border text-sm">
                      <pre className="whitespace-pre-wrap font-mono text-gray-800">
                        {result.data.content}
                      </pre>
                    </div>

                    {/* Complete conversation audio info for conversations with audio */}
                    {result.type === 'conversation_with_audio' && result.data.audio_url && (
                      <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Play className="h-4 w-4 text-purple-600" />
                            <span className="text-sm font-medium text-purple-800">
                              Complete Conversation Audio
                            </span>
                            <span className="text-xs text-purple-600">
                              (All segments stitched together)
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handlePlayAudio(result.data.audio_url)}
                              className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors flex items-center gap-1"
                            >
                              <Play className="h-3 w-3" />
                              Play Full
                            </button>
                            <a
                              href={`http://localhost:5000${result.data.audio_url}`}
                              download
                              className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors flex items-center gap-1"
                            >
                              <Download className="h-3 w-3" />
                              Download
                            </a>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Audio segments for conversations with audio */}
                    {result.data.audio_segments && result.data.audio_segments.length > 0 && (
                      <div className="mt-3">
                        <h4 className="text-sm font-medium text-gray-700 mb-2">Audio Segments:</h4>
                        <div className="space-y-2">
                          {result.data.audio_segments.map((segment, index) => (
                            <div key={index} className="flex items-center gap-3 p-2 bg-gray-50 rounded">
                              <span className="text-sm font-medium text-gray-600 min-w-0 flex-1">
                                {segment.speaker}: {segment.text.slice(0, 50)}...
                              </span>
                              <div className="flex gap-1">
                                <button
                                  onClick={() => handlePlayAudio(segment.audio_url)}
                                  className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
                                  title={`Play ${segment.speaker}'s line`}
                                >
                                  <Play className="h-3 w-3" />
                                </button>
                                <a
                                  href={`http://localhost:5000${segment.audio_url}`}
                                  download
                                  className="p-1 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded transition-colors"
                                  title="Download segment"
                                >
                                  <Download className="h-3 w-3" />
                                </a>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="text-red-700">
                    Error: {result.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default ContentGenerator;
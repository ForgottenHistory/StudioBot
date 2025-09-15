import { useState, useEffect } from 'react';
import {
  Radio,
  MessageSquare,
  Play,
  Download,
  Loader2,
  AlertCircle,
  CheckCircle,
  Mic,
  Users,
  Zap
} from 'lucide-react';

const ContentGenerator = ({
  topics,
  personalities,
  playAudio
}) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [results, setResults] = useState([]);
  const [contentTypes, setContentTypes] = useState({});
  const [selectedContentType, setSelectedContentType] = useState('ad');

  // Generic content parameters
  const [contentParams, setContentParams] = useState({
    content_type: 'ad',
    topic: '',
    personalities: [],
    custom_params: {}
  });

  // Load available content types
  useEffect(() => {
    const fetchContentTypes = async () => {
      try {
        const response = await fetch('http://localhost:5000/generate/content_types');
        const data = await response.json();
        if (data.success) {
          setContentTypes(data.content_types);
          // Set first available type as default
          const firstType = Object.keys(data.content_types)[0];
          if (firstType) {
            setSelectedContentType(firstType);
            setContentParams(prev => ({ ...prev, content_type: firstType }));
          }
        }
      } catch (error) {
        console.error('Error fetching content types:', error);
      }
    };

    fetchContentTypes();
  }, []);

  const handleGenerateContent = async () => {
    setIsGenerating(true);
    try {
      const response = await fetch('http://localhost:5000/generate/content', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(contentParams),
      });

      const result = await response.json();

      const newResult = {
        id: Date.now(),
        type: selectedContentType,
        timestamp: new Date().toLocaleTimeString(),
        params: { ...contentParams },
        success: result.success,
        data: result.success ? result : null,
        error: result.success ? null : result.error
      };

      setResults(prev => [newResult, ...prev]);

      // Reset form
      setContentParams({
        content_type: selectedContentType,
        topic: '',
        personalities: [],
        custom_params: {}
      });

    } catch (error) {
      const newResult = {
        id: Date.now(),
        type: selectedContentType,
        timestamp: new Date().toLocaleTimeString(),
        params: { ...contentParams },
        success: false,
        error: error.message
      };
      setResults(prev => [newResult, ...prev]);
    }
    setIsGenerating(false);
  };

  const handleContentTypeChange = (newType) => {
    setSelectedContentType(newType);
    setContentParams({
      content_type: newType,
      topic: '',
      personalities: [],
      custom_params: {}
    });
  };

  const handlePlayAudio = (audioUrl) => {
    if (audioUrl) {
      playAudio(audioUrl);
    }
  };

  const topicOptions = Object.keys(topics);
  const personalityOptions = Object.entries(personalities).map(([key, p]) => ({
    key: key,
    name: p.name
  }));

  // Get icon for content type
  const getContentTypeIcon = (type) => {
    switch (type) {
      case 'ad':
        return <Radio className="h-5 w-5" />;
      case 'conversation':
        return <MessageSquare className="h-5 w-5" />;
      case 'studio_interview':
        return <Mic className="h-5 w-5" />;
      default:
        return <Zap className="h-5 w-5" />;
    }
  };

  // Get button color for content type
  const getContentTypeColor = (type) => {
    switch (type) {
      case 'ad':
        return 'bg-blue-600 hover:bg-blue-700';
      case 'conversation':
        return 'bg-green-600 hover:bg-green-700';
      case 'studio_interview':
        return 'bg-purple-600 hover:bg-purple-700';
      default:
        return 'bg-gray-600 hover:bg-gray-700';
    }
  };

  // Check if content type needs multiple personalities
  const needsMultiplePersonalities = (type) => {
    return type === 'conversation' || type === 'studio_interview';
  };

  return (
    <div className="space-y-6">
      {/* Content Generation */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold text-gray-900 mb-6 flex items-center gap-2">
          <Zap className="h-5 w-5" />
          Generate Radio Content
        </h2>

        {/* Content Type Selection */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Content Type
          </label>
          <select
            value={selectedContentType}
            onChange={(e) => handleContentTypeChange(e.target.value)}
            className="w-full md:w-1/2 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
          >
            {Object.entries(contentTypes).map(([key, type]) => (
              <option key={key} value={key}>
                {type.display_name} - {type.description}
              </option>
            ))}
          </select>
        </div>

        {/* Dynamic Form Fields */}
        <div className="grid grid-cols-1 gap-4 mb-6">
          {/* Topic Selection */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Topic (optional)
            </label>
            <select
              value={contentParams.topic}
              onChange={(e) => setContentParams(prev => ({ ...prev, topic: e.target.value }))}
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

          {/* Personality Selection */}
          {needsMultiplePersonalities(selectedContentType) ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {selectedContentType === 'studio_interview' ? 'Interviewer' : 'Host'} (optional)
                </label>
                <select
                  value={contentParams.personalities[0] || ''}
                  onChange={(e) => {
                    const newPersonalities = [...contentParams.personalities];
                    newPersonalities[0] = e.target.value;
                    setContentParams(prev => ({ ...prev, personalities: newPersonalities }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
                >
                  <option value="">Auto Select</option>
                  {personalityOptions.map(p => (
                    <option key={p.key} value={p.key}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {selectedContentType === 'studio_interview' ? 'Interviewee' : 'Guest'} (optional)
                </label>
                <select
                  value={contentParams.personalities[1] || ''}
                  onChange={(e) => {
                    const newPersonalities = [...contentParams.personalities];
                    newPersonalities[1] = e.target.value;
                    setContentParams(prev => ({ ...prev, personalities: newPersonalities }));
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
                >
                  <option value="">Auto Select</option>
                  {personalityOptions.map(p => (
                    <option key={p.key} value={p.key}>
                      {p.name}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Personality (optional)
              </label>
              <select
                value={contentParams.personalities[0] || ''}
                onChange={(e) => {
                  const newPersonalities = e.target.value ? [e.target.value] : [];
                  setContentParams(prev => ({ ...prev, personalities: newPersonalities }));
                }}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent bg-white text-gray-900"
              >
                <option value="">Auto Select</option>
                {personalityOptions.map(p => (
                  <option key={p.key} value={p.key}>
                    {p.name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {/* Content Type Description */}
        {contentTypes[selectedContentType] && (
          <div className="mb-6 p-4 bg-gray-50 rounded-lg border">
            <div className="flex items-center gap-2 mb-2">
              {getContentTypeIcon(selectedContentType)}
              <h3 className="font-medium text-gray-900">
                {contentTypes[selectedContentType].display_name}
              </h3>
            </div>
            <p className="text-sm text-gray-600">
              {contentTypes[selectedContentType].description}
            </p>
            {selectedContentType === 'studio_interview' && (
              <p className="text-xs text-purple-600 mt-1">
                ✨ Uses professional studio audio effects for high-quality sound
              </p>
            )}
          </div>
        )}

        {/* Generate Button */}
        <div className="flex justify-center">
          <button
            onClick={handleGenerateContent}
            disabled={isGenerating}
            className={`px-8 py-3 text-white rounded-lg disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2 min-w-48 ${getContentTypeColor(selectedContentType)}`}
          >
            {isGenerating ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating...
              </>
            ) : (
              <>
                {getContentTypeIcon(selectedContentType)}
                Generate {contentTypes[selectedContentType]?.display_name || 'Content'}
              </>
            )}
          </button>
        </div>
      </div>

      {/* Results */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Generation Results</h3>

        {results.length === 0 ? (
          <p className="text-gray-500 text-center py-8">
            No content generated yet. Select a content type and generate some radio content above.
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
                    {getContentTypeIcon(result.type)}
                    <span className="font-medium text-gray-900">
                      {contentTypes[result.type]?.display_name || result.type} - {result.timestamp}
                    </span>
                  </div>

                  {result.success && result.data?.audio_url && (
                    <div className="flex gap-2">
                      <button
                        onClick={() => handlePlayAudio(result.data.audio_url)}
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                        title="Play Audio"
                      >
                        <Play className="h-4 w-4" />
                      </button>
                      <a
                        href={`http://localhost:5000${result.data.audio_url}`}
                        download
                        className="p-2 text-blue-600 hover:text-blue-800 hover:bg-blue-100 rounded-lg transition-colors"
                        title="Download Audio"
                      >
                        <Download className="h-4 w-4" />
                      </a>
                    </div>
                  )}
                </div>

                {result.success ? (
                  <div className="space-y-2">
                    <div className="flex flex-wrap gap-2 text-sm text-gray-600">
                      <span>Topic: {result.data.topic || 'Random'}</span>
                      {result.data.personalities && result.data.personalities.length > 0 && (
                        <>
                          <span>•</span>
                          <span>Personalities: {result.data.personalities.join(', ')}</span>
                        </>
                      )}
                      {result.data.content_type && (
                        <>
                          <span>•</span>
                          <span>Type: {contentTypes[result.data.content_type]?.display_name || result.data.content_type}</span>
                        </>
                      )}
                    </div>

                    <div className="bg-white p-3 rounded border text-sm">
                      <pre className="whitespace-pre-wrap font-mono text-gray-800">
                        {result.data.content}
                      </pre>
                    </div>

                    {/* Special highlighting for studio interviews */}
                    {result.type === 'studio_interview' && result.data.audio_url && (
                      <div className="mt-3 p-3 bg-purple-50 border border-purple-200 rounded">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-2">
                            <Mic className="h-4 w-4 text-purple-600" />
                            <span className="text-sm font-medium text-purple-800">
                              Professional Studio Quality Audio
                            </span>
                            <span className="text-xs text-purple-600">
                              ✨ Enhanced for interviews
                            </span>
                          </div>
                          <div className="flex gap-2">
                            <button
                              onClick={() => handlePlayAudio(result.data.audio_url)}
                              className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors flex items-center gap-1"
                            >
                              <Play className="h-3 w-3" />
                              Play Interview
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
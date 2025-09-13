import { useState, useEffect, useCallback } from 'react';

const BASE_URL = 'http://localhost:5000';

export const useRadioServer = () => {
  const [serverStatus, setServerStatus] = useState({
    running: false,
    data: null,
    error: null
  });

  const [topics, setTopics] = useState({});
  const [personalities, setPersonalities] = useState({});
  const [generatedContent, setGeneratedContent] = useState([]);

  const checkServerStatus = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/`);
      if (response.ok) {
        const data = await response.json();
        setServerStatus({
          running: true,
          data,
          error: null
        });
        return true;
      } else {
        throw new Error('Server returned error status');
      }
    } catch (error) {
      setServerStatus({
        running: false,
        data: null,
        error: error.message
      });
      return false;
    }
  }, []);

  const loadTopics = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/topics`);
      if (response.ok) {
        const data = await response.json();
        setTopics(data.topics || {});
      }
    } catch (error) {
      console.error('Failed to load topics:', error);
    }
  }, []);

  const loadPersonalities = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/personalities`);
      if (response.ok) {
        const data = await response.json();
        setPersonalities(data.personalities || {});
      }
    } catch (error) {
      console.error('Failed to load personalities:', error);
    }
  }, []);

  const loadGeneratedContent = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/generated_content`);
      if (response.ok) {
        const data = await response.json();
        setGeneratedContent(data.generated_content || []);
      }
    } catch (error) {
      console.error('Failed to load generated content:', error);
    }
  }, []);

  const generateAd = useCallback(async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.topic) queryParams.append('topic', params.topic);
    if (params.personality) queryParams.append('personality', params.personality);

    try {
      const response = await fetch(`${BASE_URL}/generate/dynamic_ad?${queryParams}`);
      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  const generateConversation = useCallback(async (params = {}) => {
    const queryParams = new URLSearchParams();
    if (params.host) queryParams.append('host', params.host);
    if (params.guest) queryParams.append('guest', params.guest);
    if (params.topic) queryParams.append('topic', params.topic);

    try {
      const response = await fetch(`${BASE_URL}/generate/dynamic_conversation?${queryParams}`);
      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  const generateCustomTTS = useCallback(async (text, personality) => {
    try {
      const response = await fetch(`${BASE_URL}/generate/custom_tts`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          text,
          personality
        })
      });

      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  const generateConversationWithAudio = useCallback(async (params = {}) => {
    try {
      // First generate the conversation text
      const conversationResult = await generateConversation(params);

      if (!conversationResult.success) {
        return conversationResult;
      }

      // Parse the conversation to extract individual lines
      const content = conversationResult.data.content;
      const lines = content.split('\n').filter(line => line.trim() && line.includes(':')).map(line => {
        const [speaker, ...textParts] = line.split(':');
        return {
          speaker: speaker.trim(),
          text: textParts.join(':').trim()
        };
      });

      // Generate TTS for each line
      const audioSegments = [];
      for (const line of lines) {
        const ttsResult = await generateCustomTTS(line.text, line.speaker);
        if (ttsResult.success) {
          audioSegments.push({
            ...line,
            audio_url: ttsResult.data.audio_url
          });
        }
      }

      // Create stitched complete conversation audio
      let completeAudioUrl = null;
      if (audioSegments.length > 0) {
        try {
          const stitchResponse = await fetch(`${BASE_URL}/generate/stitch_audio`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              audio_segments: audioSegments
            })
          });

          if (stitchResponse.ok) {
            const stitchData = await stitchResponse.json();
            if (stitchData.success) {
              completeAudioUrl = stitchData.audio_url;
            }
          }
        } catch (error) {
          console.warn('Failed to create complete audio:', error);
        }
      }

      return {
        success: true,
        data: {
          ...conversationResult.data,
          audio_segments: audioSegments,
          audio_url: completeAudioUrl,
          has_audio: true
        }
      };

    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [generateConversation, generateCustomTTS]);

  const controlScheduler = useCallback(async (action) => {
    try {
      const response = await fetch(`${BASE_URL}/scheduler/${action}`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  const getSchedulerStatus = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/scheduler/status`);
      if (response.ok) {
        const data = await response.json();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, []);

  const playAudio = useCallback((audioUrl) => {
    if (audioUrl) {
      const audio = new Audio(`${BASE_URL}${audioUrl}`);
      audio.play().catch(error => {
        console.error('Failed to play audio:', error);
      });
      return audio;
    }
  }, []);

  const reloadContent = useCallback(async () => {
    try {
      const response = await fetch(`${BASE_URL}/reload_content`, {
        method: 'POST'
      });

      if (response.ok) {
        const data = await response.json();
        // Refresh topics and personalities after successful reload
        loadTopics();
        loadPersonalities();
        return { success: true, data };
      } else {
        const errorData = await response.json();
        return { success: false, error: errorData.error };
      }
    } catch (error) {
      return { success: false, error: error.message };
    }
  }, [loadTopics, loadPersonalities]);

  // Auto-refresh server status
  useEffect(() => {
    checkServerStatus();
    const interval = setInterval(checkServerStatus, 2000);
    return () => clearInterval(interval);
  }, [checkServerStatus]);

  // Load data when server comes online
  useEffect(() => {
    if (serverStatus.running) {
      loadTopics();
      loadPersonalities();
      loadGeneratedContent();
    }
  }, [serverStatus.running, loadTopics, loadPersonalities, loadGeneratedContent]);

  return {
    serverStatus,
    topics,
    personalities,
    generatedContent,
    checkServerStatus,
    loadTopics,
    loadPersonalities,
    loadGeneratedContent,
    generateAd,
    generateConversation,
    generateConversationWithAudio,
    generateCustomTTS,
    controlScheduler,
    getSchedulerStatus,
    playAudio,
    reloadContent,
    BASE_URL
  };
};
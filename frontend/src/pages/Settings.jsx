import { useState, useEffect } from 'react';
import { Save, Loader2, MapPin, Clock, Link as LinkIcon, Database, Brain, Users } from 'lucide-react';
import { getSections, getLocations, getSettings, saveSettings } from '../utils/api';

export default function Settings() {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [sections, setSections] = useState([]);
  const [locations, setLocations] = useState([]);
  const [message, setMessage] = useState(null);

  const [settings, setSettings] = useState({
    default_location: '1',
    default_duration: '90',
    default_section: '',
    api_url: import.meta.env.VITE_API_URL || 'http://localhost:8002',
    model: 'local',
    ollama_url: 'http://localhost:11434',
    ollama_model: 'gemma3:12b',
    use_ai_generation: false,
    openrouter_api_key: '',
    openrouter_model: 'openrouter/auto',
    ollama_api_key: '',
  });

  // Available Ollama models
  const [ollamaModels, setOllamaModels] = useState([]);
  const [ollamaStatus, setOllamaStatus] = useState('unknown');

  useEffect(() => {
    async function loadData() {
      try {
        const [sectionsRes, locationsRes, settingsRes] = await Promise.all([
          getSections(),
          getLocations(),
          getSettings(),
        ]);
        setSections(sectionsRes.data);
        setLocations(locationsRes.data);
        
        // Load saved settings from server
        if (settingsRes.data && Object.keys(settingsRes.data).length > 0) {
          setSettings(prev => ({ ...prev, ...settingsRes.data }));
        }
      } catch (err) {
        console.error('Error loading data:', err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  // Check Ollama connection and get available models
  useEffect(() => {
    async function checkOllama() {
      if (settings.model !== 'local') {
        setOllamaStatus('not_local');
        setOllamaModels([]);
        return;
      }
      
      try {
        const response = await fetch(`${settings.ollama_url}/api/tags`);
        if (response.ok) {
          const data = await response.json();
          const models = data.models || [];
          setOllamaModels(models.map(m => m.name));
          setOllamaStatus('connected');
        } else {
          setOllamaStatus('error');
          setOllamaModels([]);
        }
      } catch (err) {
        console.error('Ollama connection error:', err);
        setOllamaStatus('error');
        setOllamaModels([]);
      }
    }
    
    if (settings.use_ai_generation) {
      checkOllama();
    }
  }, [settings.ollama_url, settings.model, settings.use_ai_generation]);

  const handleSave = async () => {
    setSaving(true);
    try {
      console.log('[DEBUG] Saving settings:', JSON.stringify(settings, null, 2));
      // Save to server for persistent, cross-device settings
      await saveSettings(settings);
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
      setTimeout(() => setMessage(null), 3000);
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="animate-spin text-scout-blue" size={32} />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <h2 className="text-2xl font-bold text-slate-800">Settings</h2>

      {message && (
        <div
          className={`p-4 rounded-lg ${
            message.type === 'success'
              ? 'bg-green-100 text-green-800'
              : 'bg-red-100 text-red-800'
          }`}
        >
          {message.text}
        </div>
      )}

      {/* Default Settings */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <Clock size={20} />
          Default Settings
        </h3>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Default Section
          </label>
          <select
            className="input-field"
            value={settings.default_section}
            onChange={(e) =>
              setSettings({ ...settings, default_section: e.target.value })
            }
          >
            <option value="">Select default section...</option>
            {sections.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name} ({s.min_age}-{s.max_age} years)
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Default Meeting Duration
          </label>
          <select
            className="input-field"
            value={settings.default_duration}
            onChange={(e) =>
              setSettings({ ...settings, default_duration: e.target.value })
            }
          >
            <option value="60">60 minutes</option>
            <option value="90">90 minutes</option>
            <option value="120">2 hours</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Default Location
          </label>
          <select
            className="input-field"
            value={settings.default_location}
            onChange={(e) =>
              setSettings({ ...settings, default_location: e.target.value })
            }
          >
            <option value="1">Chilliwack, BC</option>
            {locations
              .filter((l) => l.id !== 1)
              .map((l) => (
                <option key={l.id} value={l.id}>
                  {l.name}
                </option>
              ))}
          </select>
        </div>
      </div>

      {/* AI/Model Settings */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <Brain size={20} />
          AI Model Settings
        </h3>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            Generation Method
          </label>
          <select
            className="input-field"
            value={settings.use_ai_generation ? 'ai' : 'template'}
            onChange={(e) =>
              setSettings({ ...settings, use_ai_generation: e.target.value === 'ai' })
            }
          >
            <option value="template">Template-based (no AI)</option>
            <option value="ai">AI-powered (LLM)</option>
          </select>
          <p className="text-xs text-slate-500 mt-1">
            Template-based uses pre-defined activities. AI-powered generates custom content.
          </p>
        </div>

        {settings.use_ai_generation && (
          <>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Model Provider
              </label>
              <select
                className="input-field"
                value={settings.model}
                onChange={(e) => {
                  const newModel = e.target.value;
                  console.log('[DEBUG] Model provider changed to:', newModel);
                  const updates = { model: newModel };
                  // Auto-set URL for Ollama Cloud
                  if (newModel === 'ollama_cloud') {
                    updates.ollama_url = 'https://ollama.com/api';
                    updates.ollama_model = 'qwen3.5:397b'; // Reset to recommended model
                  }
                  setSettings(prev => ({ ...prev, ...updates }));
                }}
              >
                <option value="local">Local (Ollama)</option>
                <option value="ollama_cloud">Ollama Cloud</option>
                <option value="openrouter">OpenRouter (many models)</option>
                <option value="openai">OpenAI (GPT models)</option>
                <option value="anthropic">Anthropic (Claude)</option>
                <option value="google">Google (Gemini)</option>
              </select>
            </div>

            {settings.model === 'local' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Ollama Model
                  <span className={`ml-2 text-xs ${
                    ollamaStatus === 'connected' ? 'text-green-600' : 
                    ollamaStatus === 'error' ? 'text-red-600' : 'text-gray-500'
                  }`}>
                    ({ollamaStatus === 'connected' ? `${ollamaModels.length} models found` : 
                      ollamaStatus === 'error' ? 'connection failed' : 'checking...'})
                  </span>
                </label>
                {ollamaStatus === 'connected' && ollamaModels.length > 0 ? (
                  <select
                    className="input-field"
                    value={settings.ollama_model || ''}
                    onChange={(e) =>
                      setSettings({ ...settings, ollama_model: e.target.value })
                    }
                  >
                    {ollamaModels.map((model) => (
                      <option key={model} value={model}>{model}</option>
                    ))}
                  </select>
                ) : (
                  <input
                    type="text"
                    className="input-field"
                    value={settings.ollama_model || ''}
                    onChange={(e) =>
                      setSettings({ ...settings, ollama_model: e.target.value })
                    }
                    placeholder="gemma3:12b"
                  />
                )}
                <p className="text-xs text-slate-500 mt-1">
                  Ollama URL: {settings.ollama_url}
                </p>
              </div>
            )}

            {settings.model === 'ollama_cloud' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Ollama Cloud API Key
                </label>
                <input
                  type="password"
                  className="input-field"
                  value={settings.ollama_api_key || ''}
                  onChange={(e) =>
                    setSettings({ ...settings, ollama_api_key: e.target.value })
                  }
                  placeholder="Enter your Ollama Cloud API key"
                />
                <p className="text-xs text-slate-500 mt-1">
                  Get your API key from{" "}
                  <a
                    href="https://cloud.ollama.ai/settings/api-keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-scout-blue hover:underline"
                  >
                    cloud.ollama.ai
                  </a>
                </p>
              </div>
            )}

            {settings.model === 'ollama_cloud' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  Ollama Cloud Model
                </label>
                <select
                  className="input-field"
                  value={settings.ollama_model || 'qwen3.5:397b'}
                  onChange={(e) => {
                    console.log('[DEBUG] Ollama model changed to:', e.target.value);
                    setSettings(prev => ({ ...prev, ollama_model: e.target.value }));
                  }}
                >
                  <option value="qwen3.5:397b">First: qwen3.5:397b (Recommended)</option>
                  <option value="devstral-2:123b">Second: devstral-2:123b</option>
                  <option value="nemotron-3-super">Third: nemotron-3-super</option>
                </select>
                <p className="text-xs text-slate-500 mt-1">
                  These models are optimized for instruction following and structured tasks
                </p>
              </div>
            )}

            {settings.model === 'openrouter' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  OpenRouter API Key
                </label>
                <input
                  type="password"
                  className="input-field"
                  value={settings.openrouter_api_key || ''}
                  onChange={(e) =>
                    setSettings({ ...settings, openrouter_api_key: e.target.value })
                  }
                  placeholder="sk-or-..."
                />
                <p className="text-xs text-slate-500 mt-1">
                  Get your API key from{" "}
                  <a
                    href="https://openrouter.ai/keys"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-scout-blue hover:underline"
                  >
                    openrouter.ai
                  </a>
                </p>
              </div>
            )}

            {settings.model === 'openrouter' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  OpenRouter Model
                </label>
                <select
                  className="input-field"
                  value={settings.openrouter_model || 'openrouter/auto'}
                  onChange={(e) =>
                    setSettings({ ...settings, openrouter_model: e.target.value })
                  }
                >
                  <option value="openrouter/auto">Auto (best available)</option>
                  <option value="openrouter/openai/gpt-4o">GPT-4o</option>
                  <option value="openrouter/openai/gpt-4o-mini">GPT-4o Mini</option>
                  <option value="openrouter/anthropic/claude-3.5-sonnet">Claude 3.5 Sonnet</option>
                  <option value="openrouter/google/gemini-pro-1.5">Gemini Pro 1.5</option>
                  <option value="openrouter/meta-llama/llama-3.1-70b-instruct">Llama 3.1 70B</option>
                  <option value="openrouter/qwen/qwen3.5-32b-instruct">Qwen 3.5 32B</option>
                  <option value="openrouter/deepseek/deepseek-chat">DeepSeek Chat</option>
                </select>
              </div>
            )}

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                Ollama URL (for local models)
              </label>
              <input
                type="text"
                className="input-field"
                value={settings.ollama_url}
                onChange={(e) =>
                  setSettings({ ...settings, ollama_url: e.target.value })
                }
                placeholder="http://localhost:11434"
              />
            </div>
          </>
        )}
      </div>

      {/* API Settings */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <LinkIcon size={20} />
          API Connection
        </h3>

        <div>
          <label className="block text-sm font-medium text-slate-700 mb-1">
            API URL
          </label>
          <input
            type="text"
            className="input-field"
            value={settings.api_url}
            onChange={(e) =>
              setSettings({ ...settings, api_url: e.target.value })
            }
            placeholder="http://localhost:8002"
          />
          <p className="text-xs text-slate-500 mt-1">
            The backend API URL for fetching data and generating plans.
          </p>
        </div>
      </div>

      {/* Database Info */}
      <div className="card space-y-4">
        <h3 className="font-semibold text-slate-700 flex items-center gap-2">
          <Database size={20} />
          Database Information
        </h3>

        <div className="bg-slate-50 rounded-lg p-3 text-sm">
          <p className="text-slate-600">
            <span className="font-medium">Sections:</span> {sections.length} loaded
          </p>
          <p className="text-slate-600">
            <span className="font-medium">Locations:</span> {locations.length} loaded
          </p>
        </div>
      </div>

      {/* Save Button */}
      <button
        onClick={handleSave}
        disabled={saving}
        className="btn-primary w-full flex items-center justify-center gap-2"
      >
        {saving ? <Loader2 className="animate-spin" size={20} /> : <Save size={20} />}
        {saving ? 'Saving...' : 'Save Settings'}
      </button>

      {/* App Info */}
      <div className="text-center text-sm text-slate-500 py-4">
        <p>Scout Leader Lesson Architect v1.0.0</p>
        <p>Built with React + Vite + Tailwind</p>
      </div>
    </div>
  );
}
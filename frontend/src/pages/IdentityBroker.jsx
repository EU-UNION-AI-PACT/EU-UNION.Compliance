import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Network, Shield, Globe, ExternalLink, Github, CheckCircle, XCircle, Loader2, Play } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (typeof window !== "undefined" ? window.location.origin : "");

export default function IdentityBroker() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [providers, setProviders] = useState([]);
  const [selectedProvider, setSelectedProvider] = useState("");
  const [redirectUri, setRedirectUri] = useState("http://localhost:3003/callback");
  const [authResult, setAuthResult] = useState(null);
  const [healthStatus, setHealthStatus] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadProviders();
    loadHealthStatus();
  }, []);

  const loadProviders = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/identity-broker/providers`);
      const data = await response.json();
      setProviders(data.providers || []);
    } catch (err) {
      setError("Failed to load providers");
    }
  };

  const loadHealthStatus = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/identity-broker/health`);
      const data = await response.json();
      setHealthStatus(data);
    } catch (err) {
      console.error("Health check failed");
    }
  };

  const authenticate = async () => {
    if (!selectedProvider) {
      setError("Please select a provider");
      return;
    }

    setLoading(true);
    setError(null);
    setAuthResult(null);

    try {
      const response = await fetch(`${BACKEND_URL}/api/identity-broker/authenticate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          provider: selectedProvider,
          region_context: "global",
          client_redirect_uri: redirectUri,
          flow_type: "authentication"
        }),
      });

      if (!response.ok) {
        throw new Error('Authentication failed');
      }

      const data = await response.json();
      setAuthResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getRegionBadgeColor = (region) => {
    const colors = {
      'EU': 'bg-blue-500/20 text-blue-400 border-blue-500/50',
      'AE': 'bg-emerald-500/20 text-emerald-400 border-emerald-500/50',
      'BG': 'bg-purple-500/20 text-purple-400 border-purple-500/50',
      'SG': 'bg-orange-500/20 text-orange-400 border-orange-500/50',
      'US': 'bg-red-500/20 text-red-400 border-red-500/50',
      'BE': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      'LU': 'bg-cyan-500/20 text-cyan-400 border-cyan-500/50',
      'IL': 'bg-pink-500/20 text-pink-400 border-pink-500/50',
      'global': 'bg-slate-500/20 text-slate-400 border-slate-500/50',
      'UA': 'bg-amber-500/20 text-amber-400 border-amber-500/50',
      'CN': 'bg-red-600/20 text-red-400 border-red-600/50',
      'KR': 'bg-blue-600/20 text-blue-400 border-blue-600/50',
      'JP': 'bg-rose-500/20 text-rose-400 border-rose-500/50',
      'TW': 'bg-indigo-500/20 text-indigo-400 border-indigo-500/50',
      'EE': 'bg-sky-500/20 text-sky-400 border-sky-500/50',
      'IN': 'bg-orange-600/20 text-orange-400 border-orange-600/50',
      'CA': 'bg-red-500/20 text-red-400 border-red-500/50',
      'AU': 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50',
      'NZ': 'bg-green-500/20 text-green-400 border-green-500/50',
      'IS': 'bg-blue-400/20 text-blue-300 border-blue-400/50',
      'NO': 'bg-blue-500/20 text-blue-400 border-blue-500/50',
      'FI': 'bg-blue-600/20 text-blue-400 border-blue-600/50',
    };
    return colors[region] || colors['global'];
  };

  const getStatusBadgeColor = (status) => {
    return status === 'production' 
      ? 'bg-green-500/20 text-green-400 border-green-500/50'
      : 'bg-yellow-500/20 text-yellow-400 border-yellow-500/50';
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-white p-6 lg:p-10">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-lg border border-amber-500/50 bg-amber-500/10 flex items-center justify-center">
              <Network className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h1 className="text-3xl font-serif font-medium text-white">
                {t('identity_broker.title')}
              </h1>
              <p className="text-sm text-slate-400 font-mono">
                {t('identity_broker.subtitle')}
              </p>
            </div>
          </div>
          <p className="text-slate-400 max-w-2xl">
            {t('identity_broker.description')}
          </p>
        </div>

        {/* Health Status */}
        {healthStatus && (
          <Card className="mb-6 border-green-500/50 bg-green-500/10">
            <CardHeader>
              <div className="flex items-center gap-3">
                <CheckCircle className="w-5 h-5 text-green-500" />
                <div>
                  <CardTitle className="text-white">{t('identity_broker.health_check')}</CardTitle>
                  <CardDescription className="text-slate-400 font-mono text-xs">
                    {t('identity_broker.supported_regions')}: {healthStatus.supported_regions?.join(', ')}
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
          </Card>
        )}

        {/* Error Display */}
        {error && (
          <Card className="mb-6 border-red-500/50 bg-red-500/10">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-red-400">
                <XCircle className="w-5 h-5" />
                <span className="font-mono text-sm">{error}</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Authentication Test */}
        <Card className="mb-8 border-amber-500/50 bg-amber-500/10">
          <CardHeader>
            <CardTitle className="text-white">{t('identity_broker.test_authentication')}</CardTitle>
            <CardDescription className="text-slate-400 font-mono text-xs">
              Testen Sie die Authentifizierung mit verschiedenen Identity Providern
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {t('identity_broker.select_provider')}
                </label>
                <select
                  value={selectedProvider}
                  onChange={(e) => setSelectedProvider(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-amber-500 focus:outline-none"
                >
                  <option value="">{t('identity_broker.select_provider')}</option>
                  {providers.map((provider) => (
                    <option key={provider.id} value={provider.id}>
                      {provider.name} ({provider.region})
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  {t('identity_broker.redirect_uri')}
                </label>
                <input
                  type="text"
                  value={redirectUri}
                  onChange={(e) => setRedirectUri(e.target.value)}
                  className="w-full bg-slate-800 border border-slate-600 rounded px-3 py-2 text-white focus:border-amber-500 focus:outline-none font-mono text-sm"
                />
              </div>
              <Button
                onClick={authenticate}
                disabled={loading || !selectedProvider}
                className="bg-amber-500 hover:bg-amber-600 text-black font-mono text-sm"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    {t('identity_broker.authenticate')}...
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 mr-2" />
                    {t('identity_broker.authenticate_btn')}
                  </>
                )}
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Authentication Result */}
        {authResult && (
          <Card className="mb-8 border-green-500/50 bg-green-500/10">
            <CardHeader>
              <CardTitle className="text-white">{t('identity_broker.authentication_result')}</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">{t('identity_broker.status')}:</span>
                  <Badge className="bg-green-500/20 text-green-400 border-green-500/50 font-mono text-xs">
                    {authResult.status}
                  </Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">{t('identity_broker.provider_used')}:</span>
                  <span className="text-white font-mono text-sm">{authResult.provider_used}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-400 text-sm">{t('identity_broker.subject_id')}:</span>
                  <span className="text-white font-mono text-sm">{authResult.subject_id}</span>
                </div>
                <div>
                  <span className="text-slate-400 text-sm block mb-2">{t('identity_broker.attributes')}:</span>
                  <div className="bg-slate-800 rounded p-3">
                    <pre className="text-green-400 font-mono text-xs overflow-x-auto">
                      {JSON.stringify(authResult.attributes, null, 2)}
                    </pre>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Providers Grid */}
        <div className="mb-8">
          <h2 className="text-lg font-medium text-white mb-4">{t('identity_broker.providers')}</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {providers.map((provider) => (
              <Card key={provider.id} className="border-slate-500/50 bg-slate-500/10 hover:border-amber-500/50 transition-colors">
                <CardHeader>
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Shield className="w-5 h-5 text-amber-500" />
                      <CardTitle className="text-white text-base">{provider.name}</CardTitle>
                    </div>
                    <Badge className={`font-mono text-xs ${getStatusBadgeColor(provider.status)}`}>
                      {provider.status}
                    </Badge>
                  </div>
                  <CardDescription className="text-slate-400 font-mono text-xs">
                    {provider.type}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <Globe className="w-4 h-4 text-slate-400" />
                      <Badge className={`font-mono text-xs ${getRegionBadgeColor(provider.region)}`}>
                        {provider.region}
                      </Badge>
                    </div>
                    <div>
                      <span className="text-slate-400 text-xs block mb-1">{t('identity_broker.protocols')}:</span>
                      <div className="flex flex-wrap gap-1">
                        {provider.protocols.slice(0, 3).map((protocol) => (
                          <Badge key={protocol} variant="outline" className="text-xs border-slate-600 text-slate-300">
                            {protocol}
                          </Badge>
                        ))}
                        {provider.protocols.length > 3 && (
                          <Badge variant="outline" className="text-xs border-slate-600 text-slate-300">
                            +{provider.protocols.length - 3}
                          </Badge>
                        )}
                      </div>
                    </div>
                    <div className="flex gap-2 pt-2">
                      {provider.developer_portal && (
                        <Button
                          asChild
                          variant="outline"
                          size="sm"
                          className="flex-1 border-amber-500/50 text-amber-400 hover:bg-amber-500/10 font-mono text-xs"
                        >
                          <a 
                            href={provider.developer_portal} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-1"
                          >
                            <ExternalLink className="w-3 h-3" />
                            {t('identity_broker.developer_portal')}
                          </a>
                        </Button>
                      )}
                      {provider.github && (
                        <Button
                          asChild
                          variant="outline"
                          size="sm"
                          className="flex-1 border-slate-500/50 text-slate-300 hover:bg-slate-500/10 font-mono text-xs"
                        >
                          <a 
                            href={provider.github} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="flex items-center gap-1"
                          >
                            <Github className="w-3 h-3" />
                            GitHub
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
import React, { useState, useEffect } from "react";
import { useTranslation } from "react-i18next";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { CheckCircle, XCircle, AlertTriangle, Shield, Loader2, Download, RefreshCw, FileText, ExternalLink } from "lucide-react";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || (typeof window !== "undefined" ? window.location.origin : "");

export default function PNIACompliance() {
  const { t } = useTranslation();
  const [loading, setLoading] = useState(false);
  const [complianceData, setComplianceData] = useState(null);
  const [error, setError] = useState(null);

  const runComplianceCheck = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await fetch(`${BACKEND_URL}/api/pnia-compliance/check`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ infrastructure_config: null }),
      });

      if (!response.ok) {
        throw new Error('Compliance check failed');
      }

      const data = await response.json();
      setComplianceData(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const downloadBSIReport = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/pnia-compliance/bsi-report`);
      if (!response.ok) {
        throw new Error('BSI report not available');
      }
      const data = await response.json();
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'bsi_compliance_report.json';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      setError(err.message);
    }
  };

  useEffect(() => {
    // Mount-only bootstrap. runComplianceCheck reads stable setters from the
    // component scope; no stale-closure risk.
    runComplianceCheck();
  }, []);

  const getStatusIcon = (status) => {
    switch (status) {
      case 'PASS':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'FAIL':
        return <XCircle className="w-5 h-5 text-red-500" />;
      case 'WARN':
        return <AlertTriangle className="w-5 h-5 text-yellow-500" />;
      default:
        return null;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'PASS':
        return 'bg-green-500/10 text-green-400 border-green-500/50';
      case 'FAIL':
        return 'bg-red-500/10 text-red-400 border-red-500/50';
      case 'WARN':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/50';
      default:
        return 'bg-slate-500/10 text-slate-400 border-slate-500/50';
    }
  };

  const getOverallStatus = (status) => {
    switch (status) {
      case 'PASS':
        return {
          color: 'text-green-400',
          bg: 'bg-green-500/10',
          border: 'border-green-500/50',
          icon: <CheckCircle className="w-6 h-6" />
        };
      case 'FAIL':
        return {
          color: 'text-red-400',
          bg: 'bg-red-500/10',
          border: 'border-red-500/50',
          icon: <XCircle className="w-6 h-6" />
        };
      case 'WARN':
        return {
          color: 'text-yellow-400',
          bg: 'bg-yellow-500/10',
          border: 'border-yellow-500/50',
          icon: <AlertTriangle className="w-6 h-6" />
        };
      default:
        return {
          color: 'text-slate-400',
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/50',
          icon: null
        };
    }
  };

  return (
    <div className="min-h-screen bg-[#090d16] text-white p-6 lg:p-10">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-3 mb-4">
            <div className="w-12 h-12 rounded-lg border border-amber-500/50 bg-amber-500/10 flex items-center justify-center">
              <Shield className="w-6 h-6 text-amber-500" />
            </div>
            <div>
              <h1 className="text-3xl font-serif font-medium text-white">
                {t('pnia_compliance.title')}
              </h1>
              <p className="text-sm text-slate-400 font-mono">
                {t('pnia_compliance.subtitle')}
              </p>
            </div>
          </div>
          <p className="text-slate-400 max-w-2xl">
            {t('pnia_compliance.description')}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-3 mb-8">
          <Button
            onClick={runComplianceCheck}
            disabled={loading}
            className="bg-amber-500 hover:bg-amber-600 text-black font-mono text-sm"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                {t('pnia_compliance.checking')}
              </>
            ) : (
              <>
                <RefreshCw className="w-4 h-4 mr-2" />
                {t('pnia_compliance.run_check')}
              </>
            )}
          </Button>
          <Button
            onClick={downloadBSIReport}
            disabled={!complianceData}
            variant="outline"
            className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10 font-mono text-sm"
          >
            <Download className="w-4 h-4 mr-2" />
            {t('pnia_compliance.download_report')}
          </Button>
        </div>

        {/* PNIA Document Section */}
        <Card className="mb-8 border-amber-500/50 bg-amber-500/10">
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg border border-amber-500/50 bg-amber-500/10 flex items-center justify-center">
                <FileText className="w-5 h-5 text-amber-500" />
              </div>
              <div>
                <CardTitle className="text-white">{t('pnia_compliance.document_title')}</CardTitle>
                <CardDescription className="text-slate-400 font-mono text-xs">
                  {t('pnia_compliance.document_description')}
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-slate-300 text-sm">
                <Badge className="bg-amber-500/20 text-amber-400 border-amber-500/50 font-mono text-xs">
                  PDF
                </Badge>
                <span className="font-mono text-xs">269 KB</span>
                <span className="text-slate-500">•</span>
                <span className="font-mono text-xs">Jun 28, 2026</span>
              </div>
              <Button
                asChild
                variant="outline"
                className="border-amber-500/50 text-amber-400 hover:bg-amber-500/10 font-mono text-sm"
              >
                <a 
                  href="/documents/PNIA_Komplettpaket.pdf" 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="flex items-center gap-2"
                >
                  <ExternalLink className="w-4 h-4" />
                  {t('pnia_compliance.open_document')}
                </a>
              </Button>
            </div>
          </CardContent>
        </Card>

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

        {/* Loading State */}
        {loading && (
          <Card className="mb-6 border-amber-500/50 bg-amber-500/10">
            <CardContent className="pt-6">
              <div className="flex items-center gap-2 text-amber-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span className="font-mono text-sm">Running EU-ARF compliance check...</span>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Compliance Results */}
        {complianceData && (
          <>
            {/* Overall Status */}
            <Card className={`mb-6 border ${getOverallStatus(complianceData.status).border} ${getOverallStatus(complianceData.status).bg}`}>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    {getOverallStatus(complianceData.status).icon}
                    <div>
                      <CardTitle className={`text-xl ${getOverallStatus(complianceData.status).color}`}>
                        {complianceData.status === 'PASS' ? t('pnia_compliance.status_compliant') : complianceData.status === 'WARN' ? t('pnia_compliance.status_warning') : t('pnia_compliance.status_non_compliant')}
                      </CardTitle>
                      <CardDescription className="text-slate-400 font-mono text-xs">
                        {t('pnia_compliance.last_check')}: {new Date(complianceData.timestamp).toLocaleString()}
                      </CardDescription>
                    </div>
                  </div>
                  <Badge className={`font-mono text-xs ${getStatusColor(complianceData.status)}`}>
                    {complianceData.status}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <p className="text-slate-300 text-sm">{complianceData.summary}</p>
              </CardContent>
            </Card>

            {/* Detailed Checks */}
            <div className="grid gap-4">
              <h2 className="text-lg font-medium text-white mb-2">{t('pnia_compliance.detailed_checks')}</h2>
              {complianceData.checks.map((check, index) => (
                <Card key={check.check || `check-${index}`} className={`border ${getStatusColor(check.status)}`}>
                  <CardContent className="pt-6">
                    <div className="flex items-start gap-3">
                      <div className="mt-1">
                        {getStatusIcon(check.status)}
                      </div>
                      <div className="flex-1">
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-medium text-white">{check.check}</h3>
                          <Badge className={`font-mono text-xs ${getStatusColor(check.status)}`}>
                            {check.status}
                          </Badge>
                        </div>
                        <p className="text-slate-400 text-sm">{check.detail}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            {/* Additional Information */}
            <Card className="mt-6 border-slate-500/50 bg-slate-500/10">
              <CardHeader>
                <CardTitle className="text-white">{t('pnia_compliance.reference_standards')}</CardTitle>
                <CardDescription className="text-slate-400 font-mono text-xs">
                  Validated against eudi.dev reference implementation
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <h4 className="font-medium text-white mb-2">{t('pnia_compliance.required_standards')}</h4>
                    <ul className="space-y-1 text-slate-400">
                      <li>• Level of Assurance: High</li>
                      <li>• Hashing: SHA-256, SHA-384, SHA-512</li>
                      <li>• Signing: ES256, ES384, PS256, EdDSA</li>
                      <li>• Protocols: OIDC4VCI, OIDC4VP, MDL</li>
                    </ul>
                  </div>
                  <div>
                    <h4 className="font-medium text-white mb-2">{t('pnia_compliance.federation_requirements')}</h4>
                    <ul className="space-y-1 text-slate-400">
                      <li>• Cross-Border Enabled</li>
                      <li>• Trusted List Endpoints</li>
                      <li>• GDPR-Compliant ID Hashing</li>
                      <li>• Multi-Country Adapter Support</li>
                    </ul>
                  </div>
                </div>
              </CardContent>
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
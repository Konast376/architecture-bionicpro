import React, { useState } from 'react';
import { useKeycloak } from '@react-keycloak/web';

type ReportRow = {
  report_date: string;
  prosthesis_id: string;
  prosthesis_model: string;
  events_count: number;
  successful_actions: number;
  error_count: number;
  avg_signal_strength: number;
  avg_battery_pct: number;
  last_event_at: string;
  generated_at: string;
};

const ReportPage: React.FC = () => {
  const { keycloak, initialized } = useKeycloak();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [report, setReport] = useState<ReportRow[]>([]);
  const [requested, setRequested] = useState(false);

  const getReport = async () => {
    if (!keycloak?.token) {
      setError('Not authenticated');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      setRequested(false);

      // Backend identifies the user from JWT sub, so the UI cannot choose another user.
      const response = await fetch(`${process.env.REACT_APP_API_URL}/reports`, {
        headers: {
          Authorization: `Bearer ${keycloak.token}`,
        },
      });

      if (!response.ok) {
        const body = await response.text();
        throw new Error(`Failed to get report: HTTP ${response.status}. ${body}`);
      }

      const data: ReportRow[] = await response.json();
      setReport(data);
      setRequested(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred');
    } finally {
      setLoading(false);
    }
  };

  const downloadJson = () => {
    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'usage-report.json';
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  };

  if (!initialized) return <div>Loading...</div>;

  if (!keycloak.authenticated) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-gray-100">
        <button
          onClick={() => keycloak.login()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
        >
          Login
        </button>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto p-8 bg-white rounded-lg shadow-md">
        <h1 className="text-2xl font-bold mb-2">Usage Reports</h1>
        <p className="mb-6 text-sm text-gray-600">
          Signed in as: <strong>{String(keycloak.tokenParsed?.preferred_username || 'unknown')}</strong>
        </p>

        <div className="flex gap-3 mb-6">
          <button
            onClick={getReport}
            disabled={loading}
            className={`px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
          >
            {loading ? 'Preparing Report...' : 'Get Report'}
          </button>

          {report.length > 0 && (
            <button
              onClick={downloadJson}
              className="px-4 py-2 bg-gray-700 text-white rounded hover:bg-gray-800"
            >
              Download JSON
            </button>
          )}
        </div>

        {error && <div className="mb-6 p-4 bg-red-100 text-red-700 rounded">{error}</div>}

        {requested && report.length === 0 && !error && (
          <div className="mb-6 p-4 bg-yellow-50 text-yellow-800 rounded border border-yellow-200">
            No report data found for the current user. Check that the startup Airflow DAG finished successfully.
          </div>
        )}

        {report.length > 0 && (
          <div className="overflow-x-auto">
            <table className="min-w-full border-collapse border border-gray-300 text-sm">
              <thead>
                <tr className="bg-gray-100">
                  <th className="border p-2">Date</th>
                  <th className="border p-2">Prosthesis</th>
                  <th className="border p-2">Model</th>
                  <th className="border p-2">Events</th>
                  <th className="border p-2">Successful</th>
                  <th className="border p-2">Errors</th>
                  <th className="border p-2">Avg signal</th>
                  <th className="border p-2">Avg battery, %</th>
                  <th className="border p-2">Last event</th>
                </tr>
              </thead>
              <tbody>
                {report.map((row) => (
                  <tr key={`${row.report_date}-${row.prosthesis_id}`}>
                    <td className="border p-2">{row.report_date}</td>
                    <td className="border p-2">{row.prosthesis_id}</td>
                    <td className="border p-2">{row.prosthesis_model}</td>
                    <td className="border p-2">{row.events_count}</td>
                    <td className="border p-2">{row.successful_actions}</td>
                    <td className="border p-2">{row.error_count}</td>
                    <td className="border p-2">{row.avg_signal_strength.toFixed(2)}</td>
                    <td className="border p-2">{row.avg_battery_pct.toFixed(2)}</td>
                    <td className="border p-2">{row.last_event_at}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReportPage;

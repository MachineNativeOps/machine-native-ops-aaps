import { RefreshCw } from "lucide-react";
import ConnectionCard from "@/components/ConnectionCard";
import { useConnections } from "@/hooks/useConnections";

const availableProviders = [
  { id: "github", name: "GitHub", description: "Connect to GitHub repositories" },
  { id: "gcp", name: "Google Cloud", description: "Connect to GCP projects" },
  { id: "aws", name: "AWS", description: "Connect to AWS accounts" },
  { id: "azure", name: "Azure", description: "Connect to Azure subscriptions" },
  { id: "kubernetes", name: "Kubernetes", description: "Connect to K8s clusters" },
];

export default function ConnectionsPage() {
  const {
    connections,
    isLoading,
    connect,
    disconnect,
    upgrade,
  } = useConnections();

  const connectedProviders = new Set(
    connections.map((c) => c.provider.toLowerCase())
  );

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Connections</h1>
            <p className="text-gray-500 mt-1">
              Manage your platform integrations
            </p>
          </div>
          {isLoading && (
            <RefreshCw className="w-5 h-5 text-gray-400 animate-spin" />
          )}
        </div>

        {connections.length > 0 && (
          <div className="mb-8">
            <h2 className="text-lg font-medium text-gray-900 mb-4">
              Connected
            </h2>
            <div className="grid gap-4 md:grid-cols-2">
              {connections.map((connection) => (
                <ConnectionCard
                  key={connection.id}
                  id={connection.id}
                  provider={connection.provider}
                  accountName={connection.accountName || ""}
                  authLevel={connection.authLevel || "READ"}
                  status={connection.status}
                  capabilities={connection.capabilities || []}
                  onDisconnect={disconnect}
                  onUpgrade={upgrade}
                />
              ))}
            </div>
          </div>
        )}

        <div>
          <h2 className="text-lg font-medium text-gray-900 mb-4">
            Available Integrations
          </h2>
          <div className="grid gap-4 md:grid-cols-2">
            {availableProviders
              .filter((p) => !connectedProviders.has(p.id))
              .map((provider) => (
                <ConnectionCard
                  key={provider.id}
                  id=""
                  provider={provider.id}
                  accountName=""
                  authLevel=""
                  status="DISCONNECTED"
                  capabilities={[]}
                  onConnect={connect}
                />
              ))}
          </div>
        </div>
      </div>
    </div>
  );
}

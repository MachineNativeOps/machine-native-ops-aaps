import {
  Github,
  Cloud,
  Database,
  Server,
  Link2,
  Link2Off,
  ArrowUpCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ConnectionCardProps {
  id: string;
  provider: string;
  accountName: string;
  authLevel: string;
  status: string;
  capabilities: string[];
  onConnect?: (provider: string) => void;
  onDisconnect?: (connectionId: string) => void;
  onUpgrade?: (connectionId: string) => void;
}

const providerIcons: Record<string, React.ComponentType<{ className?: string }>> = {
  github: Github,
  gcp: Cloud,
  aws: Cloud,
  azure: Cloud,
  kubernetes: Server,
  database: Database,
};

const authLevelColors: Record<string, string> = {
  READ: "bg-blue-100 text-blue-800",
  WRITE_LOW: "bg-yellow-100 text-yellow-800",
  WRITE_HIGH: "bg-red-100 text-red-800",
};

export default function ConnectionCard({
  id,
  provider,
  accountName,
  authLevel,
  status,
  capabilities,
  onConnect,
  onDisconnect,
  onUpgrade,
}: ConnectionCardProps) {
  const Icon = providerIcons[provider.toLowerCase()] || Server;
  const isConnected = status === "ACTIVE";

  return (
    <div className="bg-white border border-gray-200 rounded-lg p-4 shadow-sm">
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-3">
          <div
            className={cn(
              "w-10 h-10 rounded-lg flex items-center justify-center",
              isConnected ? "bg-primary-100" : "bg-gray-100"
            )}
          >
            <Icon
              className={cn(
                "w-6 h-6",
                isConnected ? "text-primary-600" : "text-gray-400"
              )}
            />
          </div>
          <div>
            <h3 className="font-medium text-gray-900 capitalize">{provider}</h3>
            <p className="text-sm text-gray-500">{accountName || "Not connected"}</p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span
            className={cn(
              "px-2 py-1 text-xs font-medium rounded",
              isConnected
                ? "bg-green-100 text-green-800"
                : "bg-gray-100 text-gray-600"
            )}
          >
            {status}
          </span>
          {isConnected && (
            <span
              className={cn(
                "px-2 py-1 text-xs font-medium rounded",
                authLevelColors[authLevel] || "bg-gray-100 text-gray-600"
              )}
            >
              {authLevel}
            </span>
          )}
        </div>
      </div>

      {isConnected && capabilities && capabilities.length > 0 && (
        <div className="mt-4">
          <h4 className="text-xs font-medium text-gray-500 uppercase mb-2">
            Capabilities
          </h4>
          <div className="flex flex-wrap gap-1">
            {capabilities.map((cap) => (
              <span
                key={cap}
                className="px-2 py-0.5 text-xs bg-gray-100 text-gray-700 rounded"
              >
                {cap}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mt-4 flex gap-2">
        {isConnected ? (
          <>
            <button
              onClick={() => onDisconnect?.(id)}
              className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <Link2Off className="w-4 h-4" />
              Disconnect
            </button>
            {authLevel !== "WRITE_HIGH" && (
              <button
                onClick={() => onUpgrade?.(id)}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-primary-700 bg-primary-50 border border-primary-200 rounded-lg hover:bg-primary-100 transition-colors"
              >
                <ArrowUpCircle className="w-4 h-4" />
                Upgrade
              </button>
            )}
          </>
        ) : (
          <button
            onClick={() => onConnect?.(provider)}
            className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-white bg-primary-600 rounded-lg hover:bg-primary-700 transition-colors"
          >
            <Link2 className="w-4 h-4" />
            Connect
          </button>
        )}
      </div>
    </div>
  );
}

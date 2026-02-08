"use client";

import { useState } from "react";
import { FileText, Trash2, Loader2 } from "lucide-react";
import type { DocumentItem } from "@/lib/types/api";

function StatusBadge({ status }: { status: string }) {
  const colors: Record<string, string> = {
    completed: "bg-green-600/20 text-green-400 border-green-600/30",
    processing: "bg-yellow-600/20 text-yellow-400 border-yellow-600/30",
    failed: "bg-red-600/20 text-red-400 border-red-600/30",
  };
  const cls =
    colors[status.toLowerCase()] ||
    "bg-gray-600/20 text-gray-400 border-gray-600/30";
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${cls} inline-flex items-center gap-1`}>
      {status.toLowerCase() === "processing" && (
        <Loader2 className="h-3 w-3 animate-spin" />
      )}
      {status}
    </span>
  );
}

function FileTypeBadge({ fileType }: { fileType: string }) {
  const colors: Record<string, string> = {
    pdf: "bg-red-600/20 text-red-400 border-red-600/30",
    docx: "bg-blue-600/20 text-blue-400 border-blue-600/30",
    txt: "bg-gray-600/20 text-gray-300 border-gray-600/30",
    md: "bg-gray-600/20 text-gray-300 border-gray-600/30",
    web: "bg-purple-600/20 text-purple-400 border-purple-600/30",
    url: "bg-purple-600/20 text-purple-400 border-purple-600/30",
  };
  const cls =
    colors[fileType.toLowerCase()] ||
    "bg-gray-600/20 text-gray-400 border-gray-600/30";
  return (
    <span className={`text-xs px-2 py-0.5 rounded border ${cls} uppercase font-medium`}>
      {fileType}
    </span>
  );
}

interface DocumentCardProps {
  document: DocumentItem;
  onDelete: (id: string) => Promise<void>;
}

export function DocumentCard({ document: doc, onDelete }: DocumentCardProps) {
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleDelete = async () => {
    if (!confirming) {
      setConfirming(true);
      return;
    }
    setDeleting(true);
    try {
      await onDelete(doc.id);
    } finally {
      setDeleting(false);
      setConfirming(false);
    }
  };

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg p-4 flex flex-col justify-between hover:border-gray-700 transition-colors">
      <div>
        <div className="flex items-start justify-between mb-2">
          <div className="flex items-center gap-2 min-w-0 mr-2">
            <FileText className="h-4 w-4 text-gray-500 shrink-0" />
            <h3 className="text-sm font-medium text-gray-200 truncate">
              {doc.title}
            </h3>
          </div>
          <button
            onClick={handleDelete}
            onBlur={() => setConfirming(false)}
            disabled={deleting}
            className={`shrink-0 p-1.5 rounded transition-colors ${
              confirming
                ? "bg-red-600/20 text-red-400 hover:bg-red-600/30"
                : "text-gray-600 hover:text-gray-400 hover:bg-gray-800"
            }`}
            title={confirming ? "Click again to confirm" : "Delete document"}
          >
            {deleting ? (
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
            ) : (
              <Trash2 className="h-3.5 w-3.5" />
            )}
          </button>
        </div>

        <div className="flex flex-wrap gap-1.5 mb-3">
          <FileTypeBadge fileType={doc.file_type} />
          <StatusBadge status={doc.status} />
          {doc.subject && (
            <span className="text-xs px-2 py-0.5 rounded border bg-blue-600/10 text-blue-300 border-blue-600/20">
              {doc.subject}
            </span>
          )}
        </div>
      </div>

      <div className="flex items-center justify-between text-xs text-gray-500 mt-auto pt-2 border-t border-gray-800/50">
        <span>{doc.chunk_count} chunks</span>
        {doc.created_at && (
          <span>{new Date(doc.created_at).toLocaleDateString()}</span>
        )}
      </div>
    </div>
  );
}

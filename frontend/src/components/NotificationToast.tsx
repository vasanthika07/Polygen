import React, { useEffect } from 'react';
import { useStore } from '../store/useStore';
import { CheckCircle2, AlertTriangle, Info, X } from 'lucide-react';

export const NotificationToast: React.FC = () => {
  const { notifications, dismissNotification } = useStore();

  useEffect(() => {
    if (notifications.length > 0) {
      const timer = setTimeout(() => {
        // Auto dismiss the oldest notification after 5s
        dismissNotification(notifications[notifications.length - 1].id);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [notifications, dismissNotification]);

  if (notifications.length === 0) return null;

  return (
    <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {notifications.slice(0, 3).map((notif) => (
        <div
          key={notif.id}
          className="pointer-events-auto p-4 bg-slate-900/95 backdrop-blur-xl border border-slate-800 rounded-2xl shadow-2xl flex items-start justify-between gap-3 text-xs animate-in slide-in-from-bottom-5 duration-300"
        >
          <div className="flex items-start gap-3">
            {notif.type === 'success' && <CheckCircle2 className="w-5 h-5 text-emerald-400 shrink-0" />}
            {notif.type === 'error' && <AlertTriangle className="w-5 h-5 text-rose-400 shrink-0" />}
            {notif.type === 'warning' && <AlertTriangle className="w-5 h-5 text-amber-400 shrink-0" />}
            {notif.type === 'info' && <Info className="w-5 h-5 text-blue-400 shrink-0" />}
            <div>
              <div className="font-semibold text-white">{notif.title}</div>
              <div className="text-slate-400 text-[11px] mt-0.5 leading-relaxed">{notif.message}</div>
            </div>
          </div>
          <button
            onClick={() => dismissNotification(notif.id)}
            className="text-slate-500 hover:text-slate-300 p-1 rounded-lg"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      ))}
    </div>
  );
};


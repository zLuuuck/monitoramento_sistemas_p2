import { Icon } from '../../shared/components/Icon';

export function Card({ title, value, unit, iconName, icon, color = 'blue', subtitle, children }) {
  const cores = {
    blue: 'bg-blue-50 text-blue-600 ring-blue-100',
    green: 'bg-emerald-50 text-emerald-600 ring-emerald-100',
    red: 'bg-red-50 text-red-600 ring-red-100',
    yellow: 'bg-amber-50 text-amber-600 ring-amber-100',
    purple: 'bg-violet-50 text-violet-600 ring-violet-100',
    gray: 'bg-slate-100 text-slate-600 ring-slate-200',
  };
  const resolvedIcon = iconName || icon;

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5">
      <div className="flex justify-between items-start gap-4">
        <div className="min-w-0">
          <p className="text-slate-500 text-sm font-medium">{title}</p>
          <p className="mt-1 text-2xl md:text-3xl font-bold text-slate-900 break-words leading-tight">
            {value ?? '-'} {unit && <span className="text-base font-semibold text-slate-500">{unit}</span>}
          </p>
          {subtitle && <p className="mt-1 text-xs text-slate-500 break-words">{subtitle}</p>}
        </div>
        <div className={`${cores[color] || cores.blue} shrink-0 p-3 rounded-lg ring-1`}>
          <Icon name={resolvedIcon} size="text-xl" />
        </div>
      </div>
      {children && (
        <div className="mt-4 border-t border-slate-100 pt-4">
          {children}
        </div>
      )}
    </div>
  );
}

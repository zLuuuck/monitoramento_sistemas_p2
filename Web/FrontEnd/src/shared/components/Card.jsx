import { Icon } from '../../shared/components/Icon';

export function Card({ title, value, unit, iconName, icon, color = 'purple', subtitle, children }) {
  const cores = {
    purple: 'bg-[#4B2D6E] text-[#A855F7] ring-[#4B2D6E]',
    blue: 'bg-[#2D3A6E] text-[#6B8BFF] ring-[#2D3A6E]',
    green: 'bg-[#2D5A4E] text-[#6BFFB8] ring-[#2D5A4E]',
    red: 'bg-[#6E2D2D] text-[#FF6B6B] ring-[#6E2D2D]',
    yellow: 'bg-[#6E5A2D] text-[#FFD66B] ring-[#6E5A2D]',
    gray: 'bg-[#4A4A5A] text-[#B8B8C8] ring-[#4A4A5A]',
  };
  const resolvedIcon = iconName || icon;

  return (
    <div className="bg-[#1A1A2E] rounded-xl border border-[#2D2D44] shadow-lg p-5 hover:shadow-xl transition-all duration-300">
      <div className="flex justify-between items-start gap-4">
        <div className="min-w-0">
          <p className="text-[#8B8B9D] text-sm font-medium tracking-wide">{title}</p>
          <p className="mt-1 text-2xl md:text-3xl font-bold text-[#E2E2E8] break-words leading-tight">
            {value ?? '-'} {unit && <span className="text-base font-semibold text-[#8B8B9D]">{unit}</span>}
          </p>
          {subtitle && <p className="mt-1 text-xs text-[#8B8B9D] break-words">{subtitle}</p>}
        </div>
        <div className={`${cores[color] || cores.purple} shrink-0 p-3 rounded-xl ring-1`}>
          <Icon name={resolvedIcon} size="text-xl" />
        </div>
      </div>
      {children && (
        <div className="mt-4 border-t border-[#2D2D44] pt-4">
          {children}
        </div>
      )}
    </div>
  );
}
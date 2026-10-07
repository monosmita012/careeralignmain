import type { ReactNode } from 'react';

type SkillChipTone = 'blue' | 'green' | 'amber' | 'purple' | 'slate' | 'rose';

const toneClasses: Record<SkillChipTone, string> = {
  blue: 'border-blue-200 bg-blue-50 text-blue-800 dark:border-blue-800 dark:bg-blue-950/50 dark:text-blue-200',
  green: 'border-green-200 bg-green-50 text-green-800 dark:border-green-800 dark:bg-green-950/50 dark:text-green-200',
  amber: 'border-amber-200 bg-amber-50 text-amber-800 dark:border-amber-800 dark:bg-amber-950/50 dark:text-amber-200',
  purple: 'border-purple-200 bg-purple-50 text-purple-800 dark:border-purple-800 dark:bg-purple-950/50 dark:text-purple-200',
  slate: 'border-gray-200 bg-gray-50 text-gray-700 dark:border-gray-700 dark:bg-gray-800 dark:text-gray-200',
  rose: 'border-rose-200 bg-rose-50 text-rose-800 dark:border-rose-800 dark:bg-rose-950/50 dark:text-rose-200',
};

export default function SkillChip({ children, tone = 'blue' }: { children: ReactNode; tone?: SkillChipTone }) {
  return (
    <span className={`inline-flex max-w-full items-center rounded-full border px-2.5 py-1 text-xs font-medium leading-5 break-words ${toneClasses[tone]}`}>
      {children}
    </span>
  );
}

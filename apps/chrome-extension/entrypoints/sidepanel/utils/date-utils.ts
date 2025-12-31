export function isWeekend(date: Date): boolean {
  const day = date.getDay();
  return day === 0 || day === 6;
}

export function getPreviousWorkingDay(date: Date): Date {
  const prev = new Date(date);
  do {
    prev.setDate(prev.getDate() - 1);
  } while (isWeekend(prev));
  return prev;
}

export function getLastNWorkingDays(endDate: Date, n: number): Date[] {
  const days: Date[] = [];
  let current = new Date(endDate);

  // If start date is weekend, move back to Friday
  while (isWeekend(current)) {
    current.setDate(current.getDate() - 1);
  }

  while (days.length < n) {
    if (!isWeekend(current)) {
      days.unshift(new Date(current)); // Add to beginning to keep chronological order
    }
    current.setDate(current.getDate() - 1);
  }
  return days;
}

export function formatDate(date: Date, format: string = 'YYYY年MM月DD日'): string {
  const year = date.getFullYear();
  const month = date.getMonth() + 1;
  const day = date.getDate();

  const map: Record<string, string> = {
    'YYYY': year.toString(),
    'MM': month.toString().padStart(2, '0'),
    'DD': day.toString().padStart(2, '0'),
    'M': month.toString(),
    'D': day.toString()
  };

  return format.replace(/YYYY|MM|DD|M|D/g, (match) => map[match]);
}

export function parseDate(dateStr: string): Date | null {
  // Try parsing YYYY年MM月DD日 or YYYY-MM-DD
  let date = new Date(dateStr);
  if (!isNaN(date.getTime())) return date;

  const chineseMatch = dateStr.match(/(\d{4})年(\d{1,2})月(\d{1,2})日/);
  if (chineseMatch) {
    return new Date(parseInt(chineseMatch[1]), parseInt(chineseMatch[2]) - 1, parseInt(chineseMatch[3]));
  }
  
  return null;
}

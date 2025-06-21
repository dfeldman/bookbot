import type { Job } from '../stores/types';

export function getStatusIcon(state: string): string {
  switch (state) {
    case 'waiting': return '⏳';
    case 'running': return '⚙️';
    case 'complete': return '✅';
    case 'error': return '❌';
    case 'cancelled': return '🚫';
    default: return '❓';
  }
}

export function formatJobState(state: string): string {
  return state.charAt(0).toUpperCase() + state.slice(1);
}

export function formatJobType(jobType: string): string {
  return jobType
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

export function formatDateTime(dateString: string | null | undefined): string {
  if (!dateString) return 'N/A';
  try {
    return new Date(dateString).toLocaleString();
  } catch (e) {
    return 'Invalid Date';
  }
}

export function formatDuration(job: Job): string {
  if (!job.started_at) return 'Not started';
  
  const start = new Date(job.started_at).getTime();
  const end = job.ended_at ? new Date(job.ended_at).getTime() : Date.now();
  
  let duration = Math.max(0, end - start); // Ensure duration is not negative

  const milliseconds = Math.floor((duration % 1000));
  duration /= 1000;
  const seconds = Math.floor(duration % 60);
  duration /= 60;
  const minutes = Math.floor(duration % 60);
  duration /= 60;
  const hours = Math.floor(duration);

  let formatted = '';
  if (hours > 0) formatted += `${hours}h `;
  if (minutes > 0 || hours > 0) formatted += `${minutes}m `;
  if (seconds >= 0) formatted += `${seconds}s`;
  if (hours === 0 && minutes === 0 && seconds < 10) formatted += ` ${milliseconds}ms`;
  
  return formatted.trim() || '0s';
}

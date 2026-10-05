import { snakeToCamel, camelToSnake } from '../utils/caseTransform';

const BASE_URL = (import.meta.env.VITE_API_URL || '').replace(/\/$/, '') + '/api';

export async function fetchApi<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  try {
    let processedOptions = { ...options };

    if (processedOptions.body && typeof processedOptions.body === 'string') {
      try {
        const parsedBody = JSON.parse(processedOptions.body);
        processedOptions.body = JSON.stringify(camelToSnake(parsedBody));
      } catch (e) {
        // Body is not JSON, leave as is
      }
    }

    const response = await fetch(`${BASE_URL}${endpoint}`, {
      ...processedOptions,
      headers: {
        'Content-Type': 'application/json',
        ...processedOptions.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const detail = Array.isArray(errorData.detail)
        ? errorData.detail.map((e: any) => e.msg).join('; ')
        : errorData.detail || `Request failed with status ${response.status}`;
      throw new Error(detail);
    }

    const responseData = await response.json();
    return snakeToCamel(responseData) as T;
  } catch (error) {
    console.warn(`API call to ${endpoint} failed, falling back to local handler:`, error);
    throw error;
  }
}

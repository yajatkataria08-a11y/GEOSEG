/**
 * Convert snake_case object keys to camelCase recursively.
 */
export function snakeToCamel<T = any>(obj: any): T {
  if (Array.isArray(obj)) {
    return obj.map(snakeToCamel) as any;
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Blob) && !(obj instanceof File)) {
    return Object.keys(obj).reduce((acc: any, key: string) => {
      const camelKey = key.replace(/_([a-z0-9])/g, (_, c) => c.toUpperCase());
      acc[camelKey] = snakeToCamel(obj[key]);
      return acc;
    }, {}) as T;
  }
  return obj;
}

/**
 * Convert camelCase object keys to snake_case recursively.
 */
export function camelToSnake<T = any>(obj: any): T {
  if (Array.isArray(obj)) {
    return obj.map(camelToSnake) as any;
  }
  if (obj !== null && typeof obj === 'object' && !(obj instanceof Blob) && !(obj instanceof File) && !(obj instanceof FormData)) {
    return Object.keys(obj).reduce((acc: any, key: string) => {
      const snakeKey = key.replace(/[A-Z]/g, (c) => `_${c.toLowerCase()}`);
      acc[snakeKey] = camelToSnake(obj[key]);
      return acc;
    }, {}) as T;
  }
  return obj;
}

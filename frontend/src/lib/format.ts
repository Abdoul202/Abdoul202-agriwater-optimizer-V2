/** Format number with thousand separators (FCFA style). */
export function fcfa(value: number): string {
  return Math.round(value).toLocaleString('fr-FR');
}

/** Format number to 1 decimal place. */
export function dec1(value: number): string {
  return value.toFixed(1);
}

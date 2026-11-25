import { useTema, type Tema } from '../hooks/useTema';

/**
 * Logotipo oficial de Calles Seguras Juárez (archivos reales en public/brand/; nunca se redibuja).
 * Cada uso elige un papel y el tema activo decide el archivo:
 *  - color: encabezado y splash.
 *  - mono:  pie de página (tinta sobre papel / papel sobre grafito).
 *  - acento: /login y /registro (verde azulado sobre papel / turquesa sobre grafito).
 *  - tonal: sellos y marcas de agua (estados vacíos, pie).
 * Todas las variantes superan 3:1 contra su fondo (WCAG 2.2 AA para gráficos).
 */
export type VarianteLogo = 'color' | 'mono' | 'acento' | 'tonal';

const ARCHIVOS: Record<VarianteLogo, Record<Tema, string>> = {
  color: { light: 'logo-claro-color.svg', dark: 'logo-oscuro-color.svg' },
  mono: { light: 'logo-claro-mono-tinta.svg', dark: 'logo-oscuro-mono-papel.svg' },
  acento: { light: 'logo-claro-mono-teal.svg', dark: 'logo-oscuro-mono-turquesa.svg' },
  tonal: { light: 'logo-claro-tonal-tinta.svg', dark: 'logo-oscuro-tonal-turquesa.svg' },
};

const rutaLogo = (variante: VarianteLogo, tema: Tema) => `/brand/${ARCHIVOS[variante][tema]}`;

type Props = {
  variante?: VarianteLogo;
  /** Texto alternativo. Vacío (por defecto) cuando el logo es decorativo o el contenedor ya tiene nombre accesible. */
  alt?: string;
  className?: string;
  size?: number;
};

export function Logo({ variante = 'color', alt = '', className, size = 40 }: Props) {
  const tema = useTema();
  return (
    <img
      src={rutaLogo(variante, tema)}
      alt={alt}
      className={className}
      width={size}
      height={size}
      decoding="async"
      draggable={false}
      aria-hidden={alt ? undefined : true}
    />
  );
}

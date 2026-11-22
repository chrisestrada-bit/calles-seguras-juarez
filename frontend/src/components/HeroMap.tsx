/**
 * Mapa nocturno estilizado de Ciudad Juárez (decorativo).
 * Geografía simplificada: Río Bravo al norte, Sierra de Juárez al poniente y arterias principales.
 * Los nodos son ilustrativos: no representan reportes reales.
 */
type Nodo = { x: number; y: number; tipo: 'road' | 'manhole' | 'water'; grande?: boolean; d: number };

const NODOS: Nodo[] = [
  { x: 441, y: 214, tipo: 'water', grande: true, d: 0 },
  { x: 332, y: 184, tipo: 'road', d: 0.6 },
  { x: 449, y: 328, tipo: 'road', d: 1.2 },
  { x: 252, y: 170, tipo: 'manhole', d: 1.8 },
  { x: 586, y: 298, tipo: 'water', d: 0.9 },
  { x: 236, y: 408, tipo: 'road', d: 1.5 },
  { x: 542, y: 386, tipo: 'manhole', d: 2.2 },
];

export function HeroMap() {
  return (
    <svg className="hero-map" viewBox="0 0 640 480" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
      <defs>
        <pattern id="hm-cuadras" width="26" height="26" patternUnits="userSpaceOnUse" patternTransform="rotate(-14)">
          <path d="M0 0h26M0 0v26" className="hm-block" />
        </pattern>
        <radialGradient id="hm-fade" cx="62%" cy="52%" r="62%">
          <stop offset="0" stopColor="#fff" stopOpacity="1" />
          <stop offset="1" stopColor="#fff" stopOpacity="0" />
        </radialGradient>
        <mask id="hm-mask"><rect width="640" height="480" fill="url(#hm-fade)" /></mask>
        <linearGradient id="hm-rio" x1="0" x2="1">
          <stop offset="0" stopColor="#0b8fb0" />
          <stop offset="0.5" stopColor="#22c4e6" />
          <stop offset="1" stopColor="#0b8fb0" />
        </linearGradient>
        <linearGradient id="hm-luz" x1="0" x2="1">
          <stop offset="0" stopColor="#6ea8ff" stopOpacity="0" />
          <stop offset="0.5" stopColor="#9fc2ff" />
          <stop offset="1" stopColor="#22c4e6" stopOpacity="0" />
        </linearGradient>
        <filter id="hm-glow" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="5" /></filter>
        <filter id="hm-glow-sm" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="2.5" /></filter>
      </defs>

      {/* Traza urbana */}
      <rect width="640" height="480" fill="url(#hm-cuadras)" mask="url(#hm-mask)" />

      {/* Sierra de Juárez: curvas de nivel */}
      <g className="hm-sierra">
        <path d="M-20 300c40-30 70-20 96 8s32 70 4 104-80 40-100 30" />
        <path d="M-20 320c30-20 54-14 72 8s22 50 2 74-60 28-74 22" />
        <path d="M-20 342c20-12 36-8 48 6s14 30 0 46-38 18-48 14" />
        <path d="M-20 364c10-6 20-4 26 4s8 16 0 24-18 10-26 8" />
      </g>

      {/* Río Bravo y frontera */}
      <path id="hm-rio-path" d="M-20 70C60 40 130 95 210 80S330 40 400 70s120 60 260 50" className="hm-river-glow" filter="url(#hm-glow)" />
      <path d="M-20 70C60 40 130 95 210 80S330 40 400 70s120 60 260 50" className="hm-river" stroke="url(#hm-rio)" />
      <path d="M232 64v26M420 72v26" className="hm-bridge" />
      <text className="hm-label hm-label--river"><textPath href="#hm-rio-path" startOffset="9%">Río Bravo</textPath></text>
      <text x="300" y="44" className="hm-label hm-label--far">El Paso, Texas</text>

      {/* Arterias */}
      <g className="hm-streets">
        <path id="hm-16sep" d="M40 190C140 180 250 172 340 176" />
        <path id="hm-triunfo" d="M250 172c80 18 170 43 410 58" />
        <path id="hm-tec" d="M470 90c-15 110-30 230-40 410" />
        <path id="hm-torres" d="M120 420c160-20 330-40 540-60" />
        <path id="hm-indep" d="M560 200c20 100 40 200 60 300" />
        <path id="hm-periferico" d="M140 500c-50-100-70-200-20-300 30-50 10-90-20-140" />
        <path id="hm-juarez" d="M232 86c6 30 12 56 18 86" />
        <path id="hm-ejercito" d="M300 176c50 70 90 150 118 300" className="hm-street--minor" />
      </g>
      <g className="hm-street-labels">
        <text className="hm-label"><textPath href="#hm-triunfo" startOffset="50%">Paseo Triunfo de la República</textPath></text>
        <text className="hm-label"><textPath href="#hm-tec" startOffset="68%">Av. Tecnológico</textPath></text>
        <text className="hm-label"><textPath href="#hm-torres" startOffset="40%">Av. de las Torres</textPath></text>
        <text className="hm-label"><textPath href="#hm-periferico" startOffset="18%">Periférico Camino Real</textPath></text>
        <text className="hm-label"><textPath href="#hm-16sep" startOffset="6%">Av. 16 de Septiembre</textPath></text>
      </g>

      {/* Rutas iluminadas */}
      <g className="hm-lit">
        <path d="M250 172c80 18 170 43 410 58" className="hm-lit-base" />
        <path d="M250 172c80 18 170 43 410 58" className="hm-flow" filter="url(#hm-glow-sm)" />
        <path d="M250 172c80 18 170 43 410 58" className="hm-flow hm-flow--core" />
        <path d="M470 90c-15 110-30 230-40 410" className="hm-lit-base" />
        <path d="M470 90c-15 110-30 230-40 410" className="hm-flow hm-flow--b" filter="url(#hm-glow-sm)" />
        <path d="M470 90c-15 110-30 230-40 410" className="hm-flow hm-flow--b hm-flow--core" />
      </g>

      {/* Tu ubicación con radio de 1 km */}
      <g className="hm-me">
        <circle cx="486" cy="268" r="74" className="hm-me-radius" />
        <circle cx="486" cy="268" r="74" className="hm-me-wave" />
        <circle cx="486" cy="268" r="9" className="hm-me-halo" />
        <circle cx="486" cy="268" r="5.5" className="hm-me-dot" />
      </g>

      {/* Nodos de daños (ilustrativos) */}
      {NODOS.map((n, i) => (
        <g key={i} className={`hm-node hm-node--${n.tipo}${n.grande ? ' hm-node--big' : ''}`} style={{ ['--d' as string]: `${n.d}s` }}>
          <circle cx={n.x} cy={n.y} r={n.grande ? 22 : 15} className="hm-node-pulse" />
          <circle cx={n.x} cy={n.y} r={n.grande ? 9 : 6.5} className="hm-node-core" />
        </g>
      ))}
    </svg>
  );
}

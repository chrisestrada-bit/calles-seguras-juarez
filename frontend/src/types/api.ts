export type Rol = 'visitante' | 'ciudadano' | 'moderador' | 'coordinador';
export type TipoDano = 'Bache' | 'Alcantarilla sin tapa' | 'Encharcamiento';
export type Severidad = 'Baja' | 'Media' | 'Alta';
export type EstadoPavimento = 'Recibido' | 'Validado' | 'Programado' | 'En reparación' | 'Reparado' | 'Rechazado';
export type EstadoEncharcamiento = 'Activo' | 'Histórico' | 'Rechazado';
export type EstadoReporte = EstadoPavimento | EstadoEncharcamiento;
export type Tamano = 'chico' | 'mediano' | 'grande';
export type Profundidad = 'menos de 5 cm' | '5 a 10 cm' | 'más de 10 cm';
export type CarrilAfectado = 'carril derecho' | 'carril central' | 'carril izquierdo' | 'varios carriles' | 'acotamiento';
export type NivelAgua = 'a un lado de la calle' | 'cubre un carril' | 'a media llanta' | 'intransitable';
export type TipoConfirmacion = 'confirmacion_dano' | 'sigue_ahi' | 'ya_no_hay_agua';
export type OrigenHistorial = 'ciudadano' | 'moderacion' | 'sistema';

export interface Ubicacion { latitud: number; longitud: number; }
export interface ReferenciaCatalogo { id: number; nombre: string; }
export interface Centro { latitud: number; longitud: number; }
export interface Sector extends ReferenciaCatalogo { clave?: string; activo?: boolean; }
export interface Colonia extends ReferenciaCatalogo { codigo_postal?: string; sector: ReferenciaCatalogo; centro: Centro; activo?: boolean; }
export interface Vigencia { vigente_hasta: string; sigue_ahi: number; ya_no_hay_agua: number; }
export interface DetalleBache { tamano: Tamano; profundidad: Profundidad; carril_afectado: CarrilAfectado; }
export interface DetalleAlcantarilla { esta_senalizado: boolean; }
export interface DetalleEncharcamiento { nivel_agua: NivelAgua; hay_riesgo_personas_vehiculos: boolean | null; }
export type DetalleReporte = DetalleBache | DetalleAlcantarilla | DetalleEncharcamiento;
export interface ReportePublico {
  folio: string; tipo_dano: TipoDano; estado: EstadoReporte; etiqueta_publica: string | null; severidad: Severidad;
  ubicacion: Ubicacion; calle: string; referencia: string | null; colonia: ReferenciaCatalogo; sector: ReferenciaCatalogo;
  descripcion: string; detalle: DetalleReporte; confirmaciones: number; created_at: string; fecha_programada: string | null;
  fecha_reparacion: string | null; longevidad_dias: number | null; vigencia: Vigencia | null; es_mio?: boolean; ya_confirmado_por_mi?: boolean;
}
export interface ReporteResumenPublico {
  folio: string; tipo_dano: TipoDano; estado: EstadoReporte; etiqueta_publica: string | null; severidad: Severidad;
  ubicacion: Ubicacion; calle: string; colonia: ReferenciaCatalogo; created_at: string;
  longevidad_dias: number | null; vigencia: Vigencia | null;
}
export interface HistorialPublico { estado_anterior: EstadoReporte | null; estado_nuevo: EstadoReporte; origen: OrigenHistorial; fecha: string; }
export interface Paginacion { pagina: number; por_pagina: number; total: number; total_paginas: number; }
export interface RespuestaPaginada<T> { datos: T[]; paginacion: Paginacion; }
export interface DetalleError { campo?: string; mensaje: string; [clave: string]: unknown; }
export interface ErrorApi { codigo: string; mensaje: string; detalles: DetalleError[]; }
export interface RespuestaError { error: ErrorApi; }

export interface UsuarioResumen { id: string; nombre: string; rol: Exclude<Rol, 'visitante'>; }
export interface UsuarioRegistro extends UsuarioResumen { created_at: string; }
export interface RegistroRequest { nombre: string; correo: string; contrasena: string; }
export interface LoginRequest { correo: string; contrasena: string; }
export interface LoginResponse { access_token: string; token_type: 'bearer'; expira_en_segundos: number; usuario: UsuarioResumen; }
export interface UsuarioYo extends UsuarioResumen { correo: string; reportes_ultima_hora: number; limite_reportes_hora: number; }

export interface ReporteBacheRequest { tipo_dano: 'Bache'; latitud: number; longitud: number; colonia_id: number; calle: string; referencia?: string; descripcion?: string; tamano: Tamano; profundidad: Profundidad; carril_afectado: CarrilAfectado; forzar_nuevo: boolean; }
export interface ReporteAlcantarillaRequest { tipo_dano: 'Alcantarilla sin tapa'; latitud: number; longitud: number; colonia_id: number; calle: string; referencia?: string; descripcion?: string; esta_senalizado: boolean; forzar_nuevo: boolean; }
export interface ReporteEncharcamientoRequest { tipo_dano: 'Encharcamiento'; latitud: number; longitud: number; colonia_id: number; calle: string; referencia?: string; descripcion?: string; nivel_agua: NivelAgua; hay_riesgo_personas_vehiculos?: boolean; forzar_nuevo: boolean; }
export type CrearReporteRequest = ReporteBacheRequest | ReporteAlcantarillaRequest | ReporteEncharcamientoRequest;
export interface ReporteAutenticado extends ReportePublico { es_mio: boolean; ya_confirmado_por_mi?: boolean; }
export interface CandidatoCercano { folio: string; tipo_dano: TipoDano; estado: EstadoReporte; etiqueta_publica: string | null; severidad: Severidad; calle: string; distancia_metros: number; confirmaciones: number; ya_confirmado_por_mi: boolean; es_mio: boolean; created_at: string; }
export interface CercanosResponse { radio_metros: number; candidatos: CandidatoCercano[]; }
export interface ReporteMio extends Pick<ReporteResumenPublico, 'folio' | 'tipo_dano' | 'estado' | 'etiqueta_publica' | 'severidad' | 'calle' | 'colonia' | 'created_at' | 'longevidad_dias'> { motivo_rechazo?: string | null; es_mio: true; }
export interface HistorialResponse { folio: string; historial: HistorialPublico[]; }
export interface ConfirmacionRequest { tipo: TipoConfirmacion; }
export interface ConfirmacionResponse { folio: string; tipo: TipoConfirmacion; estado_reporte: EstadoReporte; vigencia: Vigencia; mensaje: string; }

export interface ModeracionHistorial extends HistorialPublico { actor_id: string; actor_rol: Rol; motivo: string | null; }
export interface ReporteModeracionResumen { folio: string; tipo_dano: TipoDano; estado: EstadoReporte; severidad: Severidad; calle: string; colonia: ReferenciaCatalogo; sector: ReferenciaCatalogo; confirmaciones: number; forzado_como_nuevo: boolean; autor_id: string; reportes_autor_ultimas_24h: number; created_at: string; transiciones_disponibles: EstadoReporte[]; }
export interface ReporteModeracionDetalle extends Omit<ReportePublico, 'etiqueta_publica' | 'fecha_programada' | 'fecha_reparacion' | 'longevidad_dias' | 'vigencia'> { forzado_como_nuevo: boolean; motivo_rechazo: string | null; autor_id: string; reportes_autor_ultimas_24h: number; historial: ModeracionHistorial[]; transiciones_disponibles: EstadoReporte[]; }
export interface TransicionRequest { estado_nuevo: EstadoReporte; fecha_reparacion?: string | null; motivo?: string | null; fecha_programada?: string | null; }
export interface TransicionResponse { folio: string; estado_anterior: EstadoReporte; estado: EstadoReporte; fecha_reparacion: string | null; longevidad_dias: number | null; registrado_en: string; mensaje: string; }

export interface CampoFormulario { nombre: string; etiqueta: string; tipo: 'enum' | 'booleano'; obligatorio: boolean; opciones?: string[]; visible_si?: Record<string, string>; }
export interface TipoDanoCatalogo { tipo_dano: TipoDano; prefijo_folio: 'BCH' | 'ENC'; radio_duplicados_metros: number; severidad_fija?: Severidad; vigencia_horas?: number; desmentidos_para_historico?: number; campos: CampoFormulario[]; }
export interface TiposDanoResponse { limites_territorio: { latitud_min: number; latitud_max: number; longitud_min: number; longitud_max: number }; descripcion_max_caracteres: number; datos: TipoDanoCatalogo[]; }
export interface TransicionCatalogo { desde: EstadoReporte; hacia: EstadoReporte; roles: Array<Rol | 'sistema'>; }
export interface EstadosResponse { pavimento: { estados: EstadoPavimento[]; finales: EstadoPavimento[]; transiciones: TransicionCatalogo[]; etiquetas_publicas: Record<string, string>; }; encharcamiento: { estados: EstadoEncharcamiento[]; finales: EstadoEncharcamiento[]; transiciones: TransicionCatalogo[]; }; }

export interface UsuarioAdmin extends UsuarioResumen { correo: string; activo: boolean; created_at: string; }
export interface CambiarRolRequest { rol: Exclude<Rol, 'visitante' | 'ciudadano'> | 'ciudadano'; }
export interface CambiarRolResponse { id: string; rol: Exclude<Rol, 'visitante'>; mensaje: string; }
export interface CambiarEstadoRequest { activo: boolean; }
export interface CambiarEstadoResponse { id: string; activo: boolean; mensaje: string; }
export interface SectorRequest { clave: string; nombre: string; }
export interface SectorUpdate { nombre?: string; activo?: boolean; }
export interface SectorAdmin extends Sector { clave: string; nombre: string; activo: boolean; }
export interface ColoniaRequest { sector_id: number; nombre: string; codigo_postal: string; latitud_centro: number; longitud_centro: number; }
export interface ColoniaUpdate extends Partial<ColoniaRequest> { activo?: boolean; }

export interface Periodo { desde: string; hasta: string; zona_horaria: 'America/Ciudad_Juarez'; }
export interface IndicadoresResumen { periodo: Periodo; pavimento: { total: number; por_estado: Record<EstadoPavimento, number>; por_tipo: Record<'Bache' | 'Alcantarilla sin tapa', number>; longevidad_promedio_abiertos_dias: number; tiempo_promedio_reparacion_dias: number; }; encharcamientos: { total: number; activos: number; historicos: number; intransitables: number; }; actualizado_en: string; }
export interface IndicadorSector { sector: ReferenciaCatalogo; baches_abiertos: number; reparados: number; longevidad_promedio_abiertos_dias: number; encharcamientos_total: number; encharcamientos_activos: number; }
export interface IndicadorLongevidad extends Pick<ReporteResumenPublico, 'folio' | 'tipo_dano' | 'estado' | 'severidad' | 'calle' | 'colonia' | 'created_at' | 'longevidad_dias'> {}
export interface IndicadoresModeracion { pendientes_validacion: number; antiguedad_max_pendiente_horas: number; tiempo_promedio_validacion_horas: number; rechazados_periodo: number; tasa_rechazo_pct: number; reportes_forzados_como_nuevos: number; encharcamientos_rechazados: number; }
export interface ClimaActual { temperatura_c: number; precipitacion_mm: number; descripcion: string; }
export interface PronosticoHora { hora: string; probabilidad_lluvia_pct: number; precipitacion_mm: number; }
export interface PronosticoResponse { ubicacion: string; actual: ClimaActual; proximas_horas: PronosticoHora[]; alerta_lluvia: boolean; mensaje_alerta: string | null; obtenido_en: string; desactualizado: boolean; }
export interface RiesgoCalle { calle: string; colonia: ReferenciaCatalogo; sector: ReferenciaCatalogo; nivel_riesgo: 'Alto' | 'Medio' | 'Bajo'; encharcamientos_activos: number; nivel_agua_maximo_activo: NivelAgua | null; encharcamientos_historicos_12_meses: number; ultimo_reporte: string | null; folios_activos: string[]; recomendacion: string; }
export interface RiesgoInundacionResponse { alerta_lluvia: boolean; datos: RiesgoCalle[]; criterio: string; obtenido_en: string; }
export interface GeocodingResultado { etiqueta: string; calle: string | null; ubicacion: Ubicacion; precision: 'direccion' | 'calle' | 'colonia' | 'aproximada'; colonia_sugerida: (ReferenciaCatalogo & { sector: ReferenciaCatalogo }) | null; }
export interface GeocodingResponse { fuente: 'locationiq' | 'catalogo_local'; degradado: boolean; datos: GeocodingResultado[]; atribucion: string | null; mensaje: string | null; }
export interface ColoniasResponse { datos: Colonia[]; paginacion: Paginacion; }

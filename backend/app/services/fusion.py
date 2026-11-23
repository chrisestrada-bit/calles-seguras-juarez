"""Fusión de reportes duplicados (HU-05.3), atómica: o se aplican todos los cambios o ninguno.

Reglas:
* Sólo pavimento (bache con bache, alcantarilla con alcantarilla). Los encharcamientos se resuelven con «Sigue ahí» y
  vencen solos en 6 h (RN-06), por lo que no se fusionan.
* El secundario debe estar en «Recibido» (la máquina de estados sólo permite Recibido → Rechazado, RN-05).
* El principal debe seguir abierto (Recibido, Validado, Programado o En reparación) y no puede ser el mismo folio.
* Confirmaciones: quienes confirmaron el secundario y el autor del secundario pasan a confirmar el principal, sin contar
  dos veces a quien ya lo había confirmado y nunca al autor del principal (no puede confirmar su propio reporte).
* El secundario queda «Rechazado» con motivo «Duplicado de <folio principal>», conserva su folio y apunta al principal (`reporte_principal_id`).
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errores import ErrorAPI
from app.core.tiempo import ahora_utc
from app.models import (
    ESTADOS_PAVIMENTO_ABIERTOS,
    ConfirmacionReporte,
    EstadoReporte,
    OrigenCambio,
    Reporte,
    TipoConfirmacion,
    TipoDano,
    Usuario,
)
from app.services import notificaciones, transiciones
from app.services.historial import fijar_contexto

MOTIVO_DUPLICADO = "Duplicado"


def _bloquear(db: Session, folios: list[str]) -> dict[str, Reporte]:
    # Orden determinista por id: dos fusiones cruzadas simultáneas no se bloquean mutuamente.
    filas = db.scalars(select(Reporte).where(Reporte.folio.in_(folios)).order_by(Reporte.id).with_for_update(of=Reporte)).all()
    return {r.folio: r for r in filas}


def fusionar(db: Session, actor: Usuario, folio_principal: str, folio_secundario: str) -> dict:
    if folio_principal == folio_secundario:
        raise ErrorAPI(422, "FUSION_INVALIDA", "No puedes fusionar un reporte consigo mismo.")
    try:
        reportes = _bloquear(db, [folio_principal, folio_secundario])
        principal, secundario = reportes.get(folio_principal), reportes.get(folio_secundario)
        if principal is None or secundario is None:
            faltante = folio_principal if principal is None else folio_secundario
            raise ErrorAPI(404, "NO_ENCONTRADO", f"No existe un reporte con el folio {faltante}.")
        if TipoDano.ENCHARCAMIENTO in (principal.tipo_dano, secundario.tipo_dano):
            raise ErrorAPI(422, "FUSION_INVALIDA", "Los encharcamientos no se fusionan: se confirman con «Sigue ahí» y vencen solos.")
        if principal.tipo_dano != secundario.tipo_dano:
            raise ErrorAPI(422, "FUSION_INVALIDA", "Sólo se pueden fusionar reportes del mismo tipo de daño.")
        if principal.estado not in ESTADOS_PAVIMENTO_ABIERTOS:
            raise ErrorAPI(
                409, "PRINCIPAL_NO_VALIDO",
                f"El reporte principal {principal.folio} está «{principal.estado.value}» y ya no puede recibir duplicados.",
            )
        if secundario.estado != EstadoReporte.RECIBIDO:
            raise ErrorAPI(
                409, "SECUNDARIO_NO_FUSIONABLE",
                f"Sólo se fusionan reportes «Recibido» (sin validar); {secundario.folio} está «{secundario.estado.value}».",
            )
        # RN-05: fusionar rechaza al secundario (Recibido -> Rechazado), que sólo puede hacer moderación.
        # Sin esta verificación, coordinación rechazaba reportes por esta vía (auditoría final, M3).
        transiciones.validar_transicion(secundario.tipo_dano, secundario.estado, EstadoReporte.RECHAZADO, actor.rol)

        ya_en_principal = set(
            db.scalars(select(ConfirmacionReporte.usuario_id).where(ConfirmacionReporte.reporte_id == principal.id))
        )
        del_secundario = set(
            db.scalars(
                select(ConfirmacionReporte.usuario_id).where(
                    ConfirmacionReporte.reporte_id == secundario.id,
                    ConfirmacionReporte.tipo == TipoConfirmacion.CONFIRMACION_DANO,
                )
            )
        ) | {secundario.usuario_id}
        nuevos = sorted(del_secundario - ya_en_principal - {principal.usuario_id}, key=str)
        for usuario_id in nuevos:
            db.add(
                ConfirmacionReporte(
                    reporte_id=principal.id,
                    usuario_id=usuario_id,
                    tipo=TipoConfirmacion.CONFIRMACION_DANO,
                    ciclo_vigencia=principal.ciclo_vigencia,
                )
            )
        db.flush()

        ahora = ahora_utc()
        fijar_contexto(
            db, usuario_id=actor.id, origen=OrigenCambio.MODERACION,
            motivo=f"{MOTIVO_DUPLICADO} de {principal.folio}", fecha_evento=ahora,
        )
        secundario.estado = EstadoReporte.RECHAZADO
        secundario.motivo_rechazo = f"{MOTIVO_DUPLICADO} de {principal.folio}"  # ck_rechazo_con_motivo: >= 10 caracteres
        secundario.reporte_principal_id = principal.id
        db.flush()
        notificaciones.notificar(
            db, secundario,
            f"Tu reporte {secundario.folio} se unió al reporte {principal.folio} porque describe el mismo daño. "
            f"Tu confirmación se sumó al reporte principal: dale seguimiento en {principal.folio}.",
        )
        total = len(ya_en_principal | set(nuevos))
        db.commit()
    except Exception:
        db.rollback()  # atomicidad: ninguna confirmación ni cambio de estado queda a medias
        raise
    return {
        "folio_principal": folio_principal,
        "folio_secundario": folio_secundario,
        "estado_secundario": EstadoReporte.RECHAZADO,
        "confirmaciones_transferidas": len(nuevos),
        "confirmaciones_principal": total,
        "registrado_en": ahora,
        "mensaje": f"El reporte {folio_secundario} se fusionó con {folio_principal}.",
    }

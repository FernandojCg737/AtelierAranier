from datetime import datetime, timedelta
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import bindparam, text
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_permiso
from app.core.gemini import generar_razones
from app.db.session import get_db
from app.models import Cliente, Usuario
from app.schemas.recomendaciones import (
    RecomendacionAdminOut,
    RecomendacionOut,
    RecomendacionPage,
    RecomendacionResumen,
)

router = APIRouter()

# CU18 "Recomendar Prendas por IA": el ranking (que productos recomendar y
# en que orden) lo calcula un motor de reglas en SQL --
# "comprado junto a" (co-ocurrencia en ventas de otros clientes),
# "similar a lo que ya compraste" (misma categoria/marca) y, si el cliente
# no tiene historial, los mas vendidos en general. La IA (Gemini) no elige
# los productos: solo redacta la razon personalizada de cada uno, y tiene
# una razon generica de respaldo si no hay API key o la llamada falla, asi
# que la funcionalidad nunca depende 100% de un servicio externo.

_UMBRAL_REFRESH = timedelta(hours=24)

_DETALLE_BASE = """
    SELECT dvp.id, il.producto_id, il.cantidad, v.id AS venta_id, v.cliente_id
    FROM detalle_venta_presencial dvp
    JOIN item_linea il ON il.id = dvp.id
    JOIN venta_presencial vp ON vp.id = dvp.venta_presencial_id
    JOIN venta v ON v.id = vp.id
    JOIN pago p ON p.venta_id = v.id
    WHERE p.estado = 'completado'
    UNION ALL
    SELECT dvd.id, il.producto_id, il.cantidad, v.id AS venta_id, v.cliente_id
    FROM detalle_venta_digital dvd
    JOIN item_linea il ON il.id = dvd.id
    JOIN venta_digital vd ON vd.id = dvd.venta_digital_id
    JOIN venta v ON v.id = vd.id
    JOIN pago p ON p.venta_id = v.id
    WHERE p.estado = 'completado'
"""


def _get_cliente_o_403(db: Session, usuario: Usuario) -> Cliente:
    cliente = db.query(Cliente).filter(Cliente.id == usuario.id).first()
    if cliente is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Solo los clientes tienen recomendaciones.")
    return cliente


def _historial_nombres(db: Session, cliente_id: int) -> list[str]:
    rows = db.execute(
        text(
            f"WITH dvc AS ({_DETALLE_BASE}) "
            "SELECT DISTINCT p.nombre FROM dvc JOIN producto p ON p.id = dvc.producto_id "
            "WHERE dvc.cliente_id = :cid LIMIT 5"
        ),
        {"cid": cliente_id},
    ).all()
    return [r[0] for r in rows]


def _generar_candidatos(db: Session, cliente_id: int, n: int = 8) -> list[dict]:
    compras = [
        r[0]
        for r in db.execute(
            text(f"WITH dvc AS ({_DETALLE_BASE}) SELECT DISTINCT producto_id FROM dvc WHERE cliente_id = :cid"),
            {"cid": cliente_id},
        ).all()
    ]

    candidatos: list[dict] = []
    vistos: set[int] = set(compras)

    if compras:
        co_occurrence = db.execute(
            text(
                f"""
                WITH dvc AS ({_DETALLE_BASE}),
                ventas_relacionadas AS (
                    SELECT DISTINCT venta_id FROM dvc WHERE producto_id IN :compras
                )
                SELECT dvc.producto_id, COUNT(DISTINCT dvc.venta_id) AS frecuencia
                FROM dvc
                WHERE dvc.venta_id IN (SELECT venta_id FROM ventas_relacionadas)
                  AND dvc.producto_id NOT IN :compras
                  AND EXISTS (SELECT 1 FROM producto pr WHERE pr.id = dvc.producto_id AND pr.estado = 'activo')
                  AND EXISTS (SELECT 1 FROM inventario inv WHERE inv.producto_id = dvc.producto_id AND inv.cantidad > 0)
                GROUP BY dvc.producto_id
                ORDER BY frecuencia DESC
                LIMIT 6
                """
            ).bindparams(bindparam("compras", expanding=True)),
            {"compras": compras},
        ).all()

        if co_occurrence:
            max_frec = max(f for _, f in co_occurrence)
            for producto_id, frecuencia in co_occurrence:
                candidatos.append(
                    {"producto_id": producto_id, "score": round(float(frecuencia) / max_frec, 4), "origen": "compra_conjunta"}
                )
                vistos.add(producto_id)

        if len(candidatos) < n:
            contenido = db.execute(
                text(
                    """
                    SELECT p.id, COUNT(*) AS coincidencias
                    FROM producto p
                    JOIN producto pc ON pc.id IN :compras
                    WHERE p.estado = 'activo' AND p.id NOT IN :compras
                      AND (p.categoria_id = pc.categoria_id OR p.marca_id = pc.marca_id)
                      AND EXISTS (SELECT 1 FROM inventario inv WHERE inv.producto_id = p.id AND inv.cantidad > 0)
                    GROUP BY p.id
                    ORDER BY coincidencias DESC
                    LIMIT 12
                    """
                ).bindparams(bindparam("compras", expanding=True)),
                {"compras": compras},
            ).all()
            max_coinc = max((c for _, c in contenido), default=1)
            for producto_id, coincidencias in contenido:
                if len(candidatos) >= n:
                    break
                if producto_id in vistos:
                    continue
                candidatos.append(
                    {
                        "producto_id": producto_id,
                        "score": round((float(coincidencias) / max_coinc) * 0.8, 4),
                        "origen": "similar_categoria",
                    }
                )
                vistos.add(producto_id)

    if len(candidatos) < n:
        excluidos = list(vistos) or [0]
        mas_vendidos = db.execute(
            text(
                f"""
                WITH dvc AS ({_DETALLE_BASE})
                SELECT dvc.producto_id, SUM(dvc.cantidad) AS unidades
                FROM dvc
                WHERE dvc.producto_id NOT IN :excluidos
                  AND EXISTS (SELECT 1 FROM producto pr WHERE pr.id = dvc.producto_id AND pr.estado = 'activo')
                  AND EXISTS (SELECT 1 FROM inventario inv WHERE inv.producto_id = dvc.producto_id AND inv.cantidad > 0)
                GROUP BY dvc.producto_id
                ORDER BY unidades DESC
                LIMIT 20
                """
            ).bindparams(bindparam("excluidos", expanding=True)),
            {"excluidos": excluidos},
        ).all()
        max_unidades = max((u for _, u in mas_vendidos), default=1)
        for producto_id, unidades in mas_vendidos:
            if len(candidatos) >= n:
                break
            if producto_id in vistos:
                continue
            candidatos.append(
                {"producto_id": producto_id, "score": round((float(unidades) / max_unidades) * 0.6, 4), "origen": "mas_vendido"}
            )
            vistos.add(producto_id)

    return candidatos


def _regenerar_recomendaciones(db: Session, cliente: Cliente) -> None:
    candidatos = _generar_candidatos(db, cliente.id)
    if not candidatos:
        return

    ids = [c["producto_id"] for c in candidatos]
    nombres = dict(
        db.execute(
            text("SELECT id, nombre FROM producto WHERE id IN :ids").bindparams(bindparam("ids", expanding=True)),
            {"ids": ids},
        ).all()
    )
    for c in candidatos:
        c["nombre"] = nombres.get(c["producto_id"], "")

    razones = generar_razones(cliente.nombre, _historial_nombres(db, cliente.id), candidatos)

    for c in candidatos:
        db.execute(
            text(
                """
                INSERT INTO recomendacion (cliente_id, producto_id, score, origen, fecha, razon, convertido)
                VALUES (:cliente_id, :producto_id, :score, :origen, now(), :razon, false)
                ON CONFLICT (cliente_id, producto_id) DO UPDATE SET
                    score = EXCLUDED.score, origen = EXCLUDED.origen, fecha = EXCLUDED.fecha, razon = EXCLUDED.razon
                """
            ),
            {
                "cliente_id": cliente.id,
                "producto_id": c["producto_id"],
                "score": c["score"],
                "origen": c["origen"],
                "razon": razones.get(c["producto_id"], ""),
            },
        )
    db.commit()


# ---------- Cliente ----------


@router.get("/mias", response_model=list[RecomendacionOut])
def mis_recomendaciones(
    db: Session = Depends(get_db),
    usuario: Usuario = Depends(get_current_user),
) -> list[RecomendacionOut]:
    cliente = _get_cliente_o_403(db, usuario)

    ultima = db.execute(
        text("SELECT MAX(fecha) FROM recomendacion WHERE cliente_id = :cid"), {"cid": cliente.id}
    ).scalar_one()
    if ultima is None or (datetime.utcnow() - ultima) > _UMBRAL_REFRESH:
        _regenerar_recomendaciones(db, cliente)

    filas = db.execute(
        text(
            "SELECT r.producto_id, p.nombre, r.score, r.origen, r.razon "
            "FROM recomendacion r JOIN producto p ON p.id = r.producto_id "
            "WHERE r.cliente_id = :cid ORDER BY r.score DESC"
        ),
        {"cid": cliente.id},
    ).all()

    return [
        RecomendacionOut(
            producto_id=f[0], producto_nombre=f[1], score=Decimal(str(f[2])), origen=f[3], razon=f[4] or ""
        )
        for f in filas
    ]


# ---------- Staff: Administrador (CU18) ----------


@router.get("", response_model=RecomendacionPage)
def listar_recomendaciones(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    origen: str | None = Query(default=None),
    db: Session = Depends(get_db),
    _empleado: Usuario = Depends(require_permiso("CU18")),
) -> RecomendacionPage:
    where = "1=1" if not origen else "r.origen = :origen"
    params: dict = {"origen": origen} if origen else {}

    resumen_row = db.execute(
        text(
            f"SELECT COUNT(*), COUNT(*) FILTER (WHERE r.convertido) FROM recomendacion r WHERE {where}"
        ),
        params,
    ).one()
    total_activas, convertidas = int(resumen_row[0]), int(resumen_row[1])
    tasa = round((convertidas / total_activas * 100), 1) if total_activas else 0.0

    total = db.execute(text(f"SELECT COUNT(*) FROM recomendacion r WHERE {where}"), params).scalar_one()

    rows = db.execute(
        text(
            f"""
            SELECT r.id, r.cliente_id, u.nombre, u.email, r.producto_id, p.nombre, r.score, r.origen,
                   r.razon, r.convertido, r.fecha
            FROM recomendacion r
            JOIN cliente c ON c.id = r.cliente_id
            JOIN usuario u ON u.id = c.id
            JOIN producto p ON p.id = r.producto_id
            WHERE {where}
            ORDER BY r.fecha DESC
            LIMIT :limit OFFSET :offset
            """
        ),
        {**params, "limit": page_size, "offset": (page - 1) * page_size},
    ).all()

    items = [
        RecomendacionAdminOut(
            id=r[0], cliente_id=r[1], cliente_nombre=r[2], cliente_email=r[3], producto_id=r[4],
            producto_nombre=r[5], score=Decimal(str(r[6])), origen=r[7], razon=r[8], convertido=r[9], fecha=r[10],
        )
        for r in rows
    ]

    return RecomendacionPage(
        resumen=RecomendacionResumen(total_activas=total_activas, convertidas=convertidas, tasa_conversion=tasa),
        items=items,
        total=int(total),
        page=page,
        page_size=page_size,
    )

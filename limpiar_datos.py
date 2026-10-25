"""
limpiar_datos.py - Limpia archivos CSV o Excel (.xlsx) sin modificar el original.

Uso:
    python limpiar_datos.py archivo.csv
    python limpiar_datos.py archivo.xlsx --fecha-cols "Date,Order date" --monto-cols "Amount"
    python limpiar_datos.py archivo.csv --mes-primero      (fechas tipo 3/5/24 = 5 de marzo)

Que hace:
  - Quita espacios sobrantes en todas las celdas
  - Elimina filas totalmente vacias
  - Estandariza nombres (Title Case) en columnas tipo nombre/name/cliente/customer/ciudad/city
  - Convierte fechas a formato AAAA-MM-DD en columnas tipo fecha/date
  - Convierte montos ($40, 85,5, 1.234,50) a numeros con 2 decimales
  - Elimina filas duplicadas (despues de estandarizar)
  - Guarda una copia limpia y un resumen de los cambios

Requiere:  pip install pandas openpyxl
"""

import argparse
import re
import sys
from pathlib import Path

import pandas as pd

PATRON_NOMBRE = re.compile(r"nombre|name|cliente|customer|ciudad|city", re.I)
PATRON_FECHA = re.compile(r"fecha|date", re.I)
PATRON_MONTO = re.compile(r"monto|amount|precio|price|total|importe|valor|cost", re.I)


# ----------------------------------------------------------------- lectura
def leer_archivo(ruta: Path) -> pd.DataFrame:
    """Lee CSV (probando varias codificaciones) o Excel. Todo como texto."""
    if ruta.suffix.lower() in (".xlsx", ".xlsm"):
        return pd.read_excel(ruta, dtype=str, keep_default_na=False)

    for codificacion in ("utf-8-sig", "utf-8", "latin-1"):
        try:
            return pd.read_csv(
                ruta, dtype=str, keep_default_na=False,
                encoding=codificacion, sep=None, engine="python",
            )
        except UnicodeDecodeError:
            continue
    raise ValueError("No pude leer el archivo con las codificaciones comunes.")


# ----------------------------------------------------------- limpieza base
def limpiar_texto(serie: pd.Series) -> pd.Series:
    """Quita espacios al inicio/final y dobles espacios internos."""
    return serie.astype(str).str.strip().str.replace(r"\s+", " ", regex=True)


def limpiar_nombre(valor: str) -> str:
    return valor.title() if valor else valor


def limpiar_monto(valor: str):
    """'$40' -> 40.0 | '85,5' -> 85.5 | '1.234,50' -> 1234.5 | '' -> ''"""
    if not valor:
        return ""
    v = re.sub(r"[^\d,.\-]", "", valor)  # quita simbolos de moneda y letras
    if not re.search(r"\d", v):
        return ""
    if "," in v and "." in v:
        # el ultimo separador es el decimal
        if v.rfind(",") > v.rfind("."):
            v = v.replace(".", "").replace(",", ".")
        else:
            v = v.replace(",", "")
    elif "," in v:
        # una coma con 1-2 digitos al final = decimal; si no, es miles
        if re.search(r",\d{1,2}$", v):
            v = v.replace(",", ".")
        else:
            v = v.replace(",", "")
    try:
        return round(float(v), 2)
    except ValueError:
        return ""


def limpiar_fechas(serie: pd.Series, mes_primero: bool) -> pd.Series:
    """Convierte fechas de formatos mixtos a AAAA-MM-DD. Lo que no entienda, lo deja igual."""
    es_iso = serie.str.match(r"^\d{4}-\d{1,2}-\d{1,2}$")
    resultado = pd.Series(pd.NaT, index=serie.index, dtype="datetime64[ns]")

    # las fechas que ya vienen como AAAA-MM-DD no se interpretan como dia/mes
    if es_iso.any():
        resultado[es_iso] = pd.to_datetime(serie[es_iso], format="%Y-%m-%d", errors="coerce")

    resto = (~es_iso) & (serie != "")
    if resto.any():
        resultado[resto] = pd.to_datetime(
            serie[resto], format="mixed", dayfirst=not mes_primero, errors="coerce"
        )

    texto = resultado.dt.strftime("%Y-%m-%d")
    return texto.where(resultado.notna(), serie).fillna("")


# ------------------------------------------------------------- utilidades
def columnas_por_patron(columnas, patron, manuales):
    if manuales:
        return [c for c in columnas if c in manuales]
    return [c for c in columnas if patron.search(str(c))]


def main():
    ap = argparse.ArgumentParser(description="Limpia un archivo CSV o Excel.")
    ap.add_argument("archivo", help="Ruta del archivo .csv o .xlsx")
    ap.add_argument("--fecha-cols", default="", help="Columnas de fecha, separadas por coma")
    ap.add_argument("--monto-cols", default="", help="Columnas de monto, separadas por coma")
    ap.add_argument("--nombre-cols", default="", help="Columnas de nombre, separadas por coma")
    ap.add_argument("--mes-primero", action="store_true",
                    help="Interpretar 3/5/24 como mes/dia (formato EE. UU.)")
    args = ap.parse_args()

    ruta = Path(args.archivo)
    if not ruta.exists():
        sys.exit(f"No encuentro el archivo: {ruta}")

    df = leer_archivo(ruta)
    filas_inicio = len(df)
    resumen = [f"Archivo: {ruta.name}", f"Filas al inicio: {filas_inicio}",
               f"Columnas: {', '.join(map(str, df.columns))}", ""]

    split = lambda s: [x.strip() for x in s.split(",") if x.strip()]
    cols_fecha = columnas_por_patron(df.columns, PATRON_FECHA, split(args.fecha_cols))
    cols_monto = columnas_por_patron(df.columns, PATRON_MONTO, split(args.monto_cols))
    cols_nombre = columnas_por_patron(df.columns, PATRON_NOMBRE, split(args.nombre_cols))

    # 1) espacios sobrantes
    df = df.apply(limpiar_texto)
    df = df.replace({"nan": "", "NaN": "", "None": ""})

    # 2) filas totalmente vacias
    vacias = (df == "").all(axis=1)
    n_vacias = int(vacias.sum())
    df = df[~vacias].reset_index(drop=True)
    resumen.append(f"Filas totalmente vacias eliminadas: {n_vacias}")

    # 3) nombres, fechas y montos
    for c in cols_nombre:
        df[c] = df[c].map(limpiar_nombre)
    if cols_nombre:
        resumen.append(f"Nombres estandarizados en: {', '.join(cols_nombre)}")

    for c in cols_fecha:
        df[c] = limpiar_fechas(df[c], args.mes_primero)
    if cols_fecha:
        formato = "mes/dia" if args.mes_primero else "dia/mes"
        resumen.append(f"Fechas pasadas a AAAA-MM-DD en: {', '.join(cols_fecha)} (se asumio {formato})")

    for c in cols_monto:
        df[c] = pd.to_numeric(df[c].map(limpiar_monto).replace("", pd.NA), errors="coerce")
    if cols_monto:
        resumen.append(f"Montos convertidos a numero en: {', '.join(cols_monto)}")

    # 4) duplicados (despues de estandarizar)
    antes = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    resumen.append(f"Filas duplicadas eliminadas: {antes - len(df)}")

    # 5) celdas que siguen vacias (para que el cliente decida)
    resumen.append("")
    resumen.append("Celdas vacias que quedan (revisar con el cliente):")
    hay_vacias = False
    for c in df.columns:
        n = int((df[c].isna() | (df[c] == "")).sum())
        if n:
            hay_vacias = True
            resumen.append(f"  - {c}: {n}")
    if not hay_vacias:
        resumen.append("  - ninguna")

    resumen.append("")
    resumen.append(f"Filas al final: {len(df)}")

    # guardar (el original NO se toca)
    salida = ruta.with_name(f"{ruta.stem}_limpio{ruta.suffix}")
    if ruta.suffix.lower() in (".xlsx", ".xlsm"):
        df.to_excel(salida, index=False)
    else:
        df.to_csv(salida, index=False, encoding="utf-8-sig", float_format="%.2f", na_rep="")

    ruta_resumen = ruta.with_name(f"{ruta.stem}_resumen.txt")
    ruta_resumen.write_text("\n".join(resumen), encoding="utf-8")

    print("\n".join(resumen))
    print(f"\nArchivo limpio: {salida}")
    print(f"Resumen:        {ruta_resumen}")


if __name__ == "__main__":
    main()

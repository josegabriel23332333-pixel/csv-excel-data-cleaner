# CSV / Excel Data Cleaner (Python)

A command-line tool that cleans messy CSV and Excel (`.xlsx`) files and saves a **clean copy** plus a **summary of every change**. Your original file is never modified.

## What it does

- Trims extra spaces in every cell
- Removes completely empty rows
- Standardizes names and cities (`ana lopez` -> `Ana Lopez`)
- Converts dates in mixed formats to `YYYY-MM-DD`
- Converts amounts like `$40`, `85,5` or `1.234,50` to numbers with 2 decimals
- Removes duplicate rows (after standardizing, so `ANA LOPEZ` and `ana lopez` count as the same)
- Lists the empty cells that remain, so you can decide what to do with them

## Before / After

Input (`examples/datos_desordenados.csv`):

| Name | Date | Amount | City |
|---|---|---|---|
| ana lopez | 03/05/2024 | 100 | Santo Domingo |
| ANA LOPEZ | 03/05/2024 | 100 | Santo Domingo |
| Luis P. | 2024-05-04 | | bonao |
| *(empty row)* | | | |
| luis   perez | 6 May 2024 | 85,5 | Bonao |
| maria g | 06.05.2024 | $40 | la vega |
| Maria G | 06.05.2024 | $40.00 | La Vega |
| carlos r | 07/05/2024 | 1.234,50 | |

Output (`examples/datos_desordenados_limpio.csv`):

| Name | Date | Amount | City |
|---|---|---|---|
| Ana Lopez | 2024-05-03 | 100.00 | Santo Domingo |
| Luis P. | 2024-05-04 | | Bonao |
| Luis Perez | 2024-05-06 | 85.50 | Bonao |
| Maria G | 2024-05-06 | 40.00 | La Vega |
| Carlos R | 2024-05-07 | 1234.50 | |

8 rows became 5: 1 empty row and 2 duplicates were removed. See `examples/datos_desordenados_resumen.txt` for the generated summary.

## Installation

Requires Python 3.9+.

```bash
pip install -r requirements.txt
```

## Usage

```bash
python limpiar_datos.py file.csv
python limpiar_datos.py file.xlsx --fecha-cols "Date,Order date" --monto-cols "Amount"
python limpiar_datos.py file.csv --mes-primero
```

The tool creates two new files next to the original:

- `file_limpio.csv` (or `.xlsx`): the cleaned data
- `file_resumen.txt`: what was changed

### Options

| Option | Description |
|---|---|
| `--fecha-cols` | Date columns, comma-separated (default: columns whose name contains `fecha` or `date`) |
| `--monto-cols` | Amount columns, comma-separated (default: names containing `monto`, `amount`, `precio`, `price`, `total`, `importe`, `valor`, `cost`) |
| `--nombre-cols` | Name columns, comma-separated (default: names containing `nombre`, `name`, `cliente`, `customer`, `ciudad`, `city`) |
| `--mes-primero` | Read `03/05/2024` as month/day (US format). Default is day/month |

## Limitations (read before using on real data)

- **Ambiguous dates:** `03/05/2024` can be 3 May or 5 March. The tool assumes day/month unless you use `--mes-primero`. Always confirm the format with the data owner.
- **Name capitalization:** names are converted to Title Case, so names like `McDonald` become `Mcdonald`. Review names after cleaning.
- **Column detection is by name.** If your columns are named differently, pass them with the options above.
- **Empty cells are not guessed or filled.** They are reported in the summary.
- An existing `file_limpio` output is overwritten when you run the tool again.
- Always review the cleaned file before using it.

## Privacy

Do not commit real customer data to this repository. The `.gitignore` excludes `*_limpio.*` and `*_resumen.txt` files (except the demos in `examples/`).

The messages printed in the terminal and in the summary are in Spanish.

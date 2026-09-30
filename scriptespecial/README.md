# scriptespecial: ¿quién no me sigue de vuelta en Instagram?

Este script compara tus **seguidores** con las cuentas que **sigues** y te muestra
las que tú sigues pero que **no te siguen**.

Funciona con el archivo oficial que te da Instagram ("Descargar tu información").
**No pide tu contraseña y no se conecta a tu cuenta**, así que no hay riesgo de bloqueo.

## Requisitos

- Python 3.8 o superior (no hay que instalar nada más).
  Comprueba con `python --version` (en Mac/Linux, `python3 --version`).

## Paso 1: descargar tus datos de Instagram

Los nombres de los menús pueden cambiar un poco según la versión de la app.

1. Instagram → **Configuración** → **Centro de cuentas**.
2. **Tu información y permisos** → **Descargar tu información**.
3. **Descargar o transferir información** → elige tu cuenta.
4. Elige **Parte de tu información** y marca solo **Seguidores y seguidos**.
5. **Descargar en el dispositivo**, rango **Desde el principio**, formato **JSON**.
6. Envía la solicitud. Instagram te avisa cuando esté lista (puede tardar de minutos a horas).
7. Descarga el `.zip`.

## Paso 2: ejecutar el script

Opción A: con el `.zip` directamente (lo más fácil):

```bash
cd scriptespecial
python no_me_siguen.py "C:\ruta\al\instagram-tuusuario.zip"
```

Opción B: descomprime el `.zip` dentro de la carpeta `datos/` y ejecuta:

```bash
cd scriptespecial
python no_me_siguen.py
```

## Paso 3: ver el resultado

El script imprime la lista en pantalla y crea la carpeta `resultados/` con:

| Archivo | Para qué sirve |
|---|---|
| `no_me_siguen.html` | Ábrelo en el navegador: cada usuario es un enlace a su perfil y tiene una casilla **"Ya lo dejé"** para ir llevando la cuenta (se guarda en tu navegador). |
| `no_me_siguen.csv` | Para abrir en Excel. |
| `no_me_siguen.txt` | Lista simple de usuarios. |

## Cuentas que quieres conservar

Si sigues a alguien a propósito aunque no te siga (un artista, una marca, un maestro),
escribe su usuario en `excepciones.txt`, uno por línea. El script no lo mostrará
como "creído".

## Probarlo con datos de ejemplo

```bash
python no_me_siguen.py ejemplo
```

Los datos de `ejemplo/` son inventados. Debe mostrar `creido_1`, `creido_2` y `banda_favorita`.

## Privacidad

Tus archivos de `datos/` y tus `resultados/` contienen información personal.
El archivo `.gitignore` del repositorio evita que se suban a GitHub. No los quites de ahí.

## Limitaciones

- El resultado es una "foto" del momento en que pediste la descarga. Si alguien te
  siguió o dejó de seguirte después, vuelve a descargar los datos.
- Instagram puede cambiar el formato de sus archivos. Si el script dice que no
  encuentra usuarios, avísame con el mensaje de error.

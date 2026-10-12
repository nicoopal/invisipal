# Invisipal

**Una guía de reunión privada, estilo teleprompter. Vos ves tus notas; quienes miran la pantalla compartida, no.**

[English](README.md) · [Documentación completa](README.md) · [Preguntas frecuentes](docs/faq.md)

Invisipal es una ventana oscura, translúcida, siempre visible y sin bordes que muestra tus notas **de a una tarjeta por vez** ("3 / 10"). Le pide a Windows que la excluya de la captura de pantalla (`SetWindowDisplayAffinity` con `WDA_EXCLUDEFROMCAPTURE`), así que al **compartir la pantalla completa** en Teams, Zoom, Google Meet u OBS, la ventana no forma parte de la imagen que reciben los demás.

Solo usa la biblioteca estándar de Python (tkinter + ctypes): cero dependencias.

## Requisitos

- Windows 10 versión 2004 o superior, o Windows 11. En builds anteriores de Windows 10 la ventana se ve como un rectángulo negro (el indicador dice `● blacked out`).
- Python 3.10+ (con tkinter, incluido en el instalador de python.org), o el `.exe` de la [página de releases](https://github.com/nicoopal/invisipal/releases), que no necesita Python.

## Cómo ejecutarlo

```powershell
git clone https://github.com/nicoopal/invisipal.git
cd invisipal
pythonw invisipal.pyw        # sin ventana de consola
# o bien:  python -m invisipal
```

También sirve hacer doble clic en `invisipal.pyw`, o ejecutar `Invisipal.exe` si se descargó el release.

Si ya está abierto, volver a lanzarlo solo muestra la ventana existente. Opciones de línea de comandos: `--data-dir CARPETA`, `--guide ARCHIVO`, `--no-protect` (deja la ventana visible para los demás; útil para capturas y demos) y `--version`.

## Atajos

### Globales (funcionan sin que la ventana tenga foco)

| Atajo | Acción |
|---|---|
| `Ctrl+Alt+→` / `Ctrl+Alt+←` | Tarjeta siguiente / anterior (en una tarjeta larga, primero baja o sube una página) |
| `Ctrl+Alt+Inicio` / `Ctrl+Alt+Fin` | Primera / última tarjeta |
| `Ctrl+Alt+↑` / `Ctrl+Alt+↓` | Letra más grande / más chica |
| `Ctrl+Alt+RePág` / `Ctrl+Alt+AvPág` | Más opaca / más transparente |
| `Ctrl+Alt+H` | Mostrar / ocultar (sin robar el foco) |
| `Ctrl+Alt+T` | Modo "click-through": el mouse atraviesa la ventana |
| `Ctrl+Alt+G` | Pasar a la siguiente guía |
| `Ctrl+Alt+S` | Iniciar / pausar el cronómetro |
| `Ctrl+Alt+R` | Recargar la guía desde el disco |
| `Ctrl+Alt+Q` | Salir |

Todos se pueden cambiar en `config.json` (sección `hotkeys`); un valor `""` desactiva el atajo.

### Con la ventana enfocada

`→`, `Espacio`, `AvPág` siguiente · `←`, `Retroceso`, `RePág` anterior · `Inicio` / `Fin` primera / última · `+` / `-` tamaño de letra · `E` editar (`Ctrl+S` guarda, `Esc` cancela) · `L` biblioteca de guías · `Ctrl+V` pega el portapapeles como una guía nueva · `F5` recargar · `?` ayuda con todos los atajos.

Con el mouse: arrastrar el encabezado para mover, arrastrar `◢` para cambiar el tamaño, `Ctrl`+rueda para el tamaño de letra, `Alt`+rueda para la opacidad, doble clic en el cronómetro para reiniciarlo.

### Teclados con AltGr (español latinoamericano, alemán, etc.)

Windows interpreta AltGr como `Ctrl+Alt`. Un atajo global `Ctrl+Alt+Q` impediría escribir `@` (que en estos teclados es `AltGr+Q`) en cualquier programa. Por eso Invisipal detecta cuándo una combinación `Ctrl+Alt+tecla` escribe un carácter en el teclado activo y, en ese caso, registra automáticamente `Ctrl+Alt+Shift+tecla` (por ejemplo `Ctrl+Alt+Shift+Q` para salir). La ayuda (`?`) muestra la combinación realmente vigente. Se controla con `avoid_altgr_conflicts` (por defecto `true`).

Si en la ayuda un atajo aparece como `(in use by another app)`, otro programa lo tiene reservado. Algunos drivers de gráficos Intel usan `Ctrl+Alt+flechas` para rotar la pantalla: desactivar esos atajos en el panel de Intel o cambiar el atajo en `config.json`.

## Cómo escribir tarjetas

Las guías son archivos `.md` o `.txt` dentro de la carpeta `guides/`, un archivo por reunión. Una línea que contenga solamente `---` empieza una tarjeta nueva:

```markdown
# Apertura
Gracias por el tiempo. El objetivo de hoy: salir con una decisión.

---

## Agenda
1. Estado
2. Decisión
3. Próximos pasos
```

Si no hay `---`, se divide por títulos (`#` o `##`); si tampoco hay títulos, por párrafos (líneas en blanco). Se entiende un Markdown básico: títulos, listas, listas de tareas (`- [ ]`), citas, código, `**negrita**`, `*cursiva*`, `==resaltado==` y `~~tachado~~`. No hay tablas, imágenes ni links; conviene evitar emojis.

Atajos para crear guías: copiar un texto y apretar `Ctrl+V` en Invisipal lo convierte en una guía nueva; `L` abre la biblioteca; `E` abre el editor integrado. Además, cualquier editor externo (VS Code, Bloc de notas) sirve: Invisipal recarga el archivo solo cuando cambia. Ejemplo incluido: [`guides/guia.txt`](guides/guia.txt).

Todo (editor, biblioteca, ayuda) ocurre dentro de la misma ventana protegida a propósito: los popups o menús serían ventanas aparte, y esas sí se capturarían.

## Dónde se guardan los datos

Todo se guarda en **`Documentos\Invisipal`**: `config.json` (posición, tamaño, letra, opacidad, atajos) y la carpeta `guides\` con una guía por reunión. La carpeta se crea sola la primera vez, con las guías de ejemplo. Si Documentos está en OneDrive, las guías quedan sincronizadas. Actualizar o reinstalar Invisipal no toca esa carpeta. Para el modo portable (todo junto a la app, por ejemplo en un pendrive), crear un archivo vacío llamado `portable` junto a `invisipal.pyw` o `Invisipal.exe`. `--data-dir` permite usar cualquier otra carpeta. La configuración completa está documentada en el [README en inglés](README.md#configuration).

La ventana no aparece en la barra de tareas ni en Alt+Tab (`show_in_taskbar: false`), porque la barra de tareas sí forma parte de lo que se comparte.

## Cómo probar que es invisible

Conviene hacerlo antes de cualquier reunión importante.

1. Crear una reunión de Teams (o Zoom, o Meet) y entrar desde la PC.
2. Entrar a la misma reunión desde el celular, como segundo participante (con micrófono y parlante silenciados para evitar acople).
3. En la PC, **compartir la pantalla completa** (no una sola ventana).
4. Abrir Invisipal y ponerlo sobre el contenido compartido.
5. Mirar el celular: se ve el escritorio, pero **no se ve Invisipal**.

Prueba rápida sin reunión: `Win+Shift+S`, recortar un rectángulo sobre la ventana de Invisipal; en la imagen debería verse lo que hay detrás, no la ventana.

El indicador del encabezado lo resume: `● private` (verde) significa oculta a la captura; `● blacked out` es un Windows 10 anterior a 2004 (se ve negra); `● VISIBLE` significa que no hay protección (por ejemplo con `--no-protect`).

## Limitaciones

Solo protege contra la captura por software. No sirve contra un celular que filme la pantalla, ni contra una capturadora HDMI, ni contra una persona mirando el monitor. Si se comparte una ventana puntual en lugar de la pantalla completa, Invisipal no interviene. Escritorio remoto y máquinas virtuales pueden comportarse distinto. Usar con criterio: es para notas y guiones propios, y hay que respetar las reglas de entrevistas, exámenes o cualquier situación donde no se permitan ayudas ocultas.

Documentación completa, cómo funciona por dentro y solución de problemas: [README.md](README.md), [docs/how-it-works.md](docs/how-it-works.md) y [docs/faq.md](docs/faq.md).

## Licencia

MIT. Copyright (c) 2026 Nico Palermo.

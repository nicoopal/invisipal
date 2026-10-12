# Invisipal

**Una guía de reunión privada, estilo teleprompter. Vos ves tus notas; quienes miran la pantalla compartida, no.**

[English](README.md) · [Documentación completa](README.md) · [Preguntas frecuentes](docs/faq.md)

Invisipal es una ventana oscura, translúcida, siempre visible y sin bordes que muestra tus notas **de a una tarjeta por vez** ("3 / 10"). Le pide a Windows que la excluya de la captura de pantalla (`SetWindowDisplayAffinity` con `WDA_EXCLUDEFROMCAPTURE`), así que al **compartir la pantalla completa** en Teams, Zoom, Google Meet u OBS, la ventana no forma parte de la imagen que reciben los demás.

Solo usa la biblioteca estándar de Python (tkinter + ctypes): cero dependencias.

## Cómo instalarlo

Invisipal funciona con Python, que corre en cualquier PC con Windows, incluso en las que Smart App Control bloquea los programas sin firma.

1. **Bajá [`Invisipal.zip`](https://github.com/nicoopal/invisipal/releases/latest/download/Invisipal.zip)** y descomprimilo donde quieras (clic derecho → *Extraer todo*).
2. **Hacé doble clic en `Install Invisipal.pyw`**, dentro de la carpeta descomprimida.
3. Tocá **Instalar**. Invisipal queda en el menú Inicio y en el escritorio; abrilo desde ahí.

**¿No tenés Python?** Bajalo de **[python.org/downloads](https://www.python.org/downloads/)** (versión 3.10 o más nueva), instalalo con las opciones que vienen marcadas y volvé al paso 2.

No hace falta ser administrador. El instalador copia la app a `%LOCALAPPDATA%\Invisipal\app` y crea accesos directos que la abren con `pythonw.exe`; tus guías y tu configuración quedan en `Documentos\Invisipal`. Para **actualizar**, bajá el zip nuevo y volvé a ejecutar `Install Invisipal.pyw`. Para **desinstalar**, ejecutalo y tocá **Desinstalar** (tus guías no se borran).

Requiere Windows 10 versión 2004 o superior, o Windows 11. En versiones anteriores de Windows 10 la ventana se ve como un rectángulo negro al compartir (el indicador dice `● blacked out`).

**Otras formas de usarlo:**

- **Sin instalar**: doble clic en `invisipal.pyw` dentro de la carpeta descomprimida, o desde un clon del repo con `pythonw invisipal.pyw`.
- **`.exe` sin Python**: cada release también trae un [instalador](https://github.com/nicoopal/invisipal/releases/latest/download/Invisipal-Setup.exe) y un [`.exe` portable](https://github.com/nicoopal/invisipal/releases/latest/download/Invisipal-portable.exe). Todavía no están firmados: Windows SmartScreen avisa (*Más información → Ejecutar de todas formas*) y **Smart App Control los bloquea** con *"An Application Control policy has blocked this file"*. En ese caso, usá la versión con Python.

Si Invisipal ya está abierto, volver a abrirlo solo muestra la ventana existente. Opciones de línea de comandos: `--data-dir CARPETA`, `--guide ARCHIVO`, `--no-protect` (deja la ventana visible para los demás; útil para capturas y demos) y `--version`.

## Atajos

### Globales (funcionan sin que la ventana tenga foco)

| Atajo | Acción |
|---|---|
| `Ctrl+Alt+→` / `Ctrl+Alt+←` | Tarjeta siguiente / anterior (en una tarjeta larga, primero baja o sube una página) |
| `Ctrl+Alt+Inicio` / `Ctrl+Alt+Fin` | Primera / última tarjeta |
| `Ctrl+Alt+↑` / `Ctrl+Alt+↓` | Letra más grande / más chica |
| `Ctrl+Alt+RePág` / `Ctrl+Alt+AvPág` | Fondo más opaco / más transparente |
| `Ctrl+Alt+Shift+→` / `Ctrl+Alt+Shift+←` | Texto más opaco / más transparente |
| `Ctrl+Alt+Shift+Inicio` / `RePág` / `Fin` / `AvPág` | Mover a la esquina superior izquierda / superior derecha / inferior derecha / inferior izquierda |
| `Ctrl+Alt+Shift+↑` / `Ctrl+Alt+Shift+↓` | Mover arriba al centro (debajo de la cámara) / abajo al centro |
| `Ctrl+Alt+I` | Mostrar / ocultar el índice de tarjetas |
| `Ctrl+Alt+H` | Mostrar / ocultar (sin robar el foco) |
| `Ctrl+Alt+T` | Modo "click-through": el mouse atraviesa la ventana |
| `Ctrl+Alt+G` | Pasar a la siguiente guía |
| `Ctrl+Alt+S` | Iniciar / pausar el cronómetro |
| `Ctrl+Alt+R` | Recargar la guía desde el disco |
| `Ctrl+Alt+Q` | Salir |

Todos se pueden cambiar en `config.json` (sección `hotkeys`); un valor `""` desactiva el atajo.

### Con la ventana enfocada

`→`, `Espacio`, `AvPág` siguiente · `←`, `Retroceso`, `RePág` anterior · `Inicio` / `Fin` primera / última · `+` / `-` tamaño de letra · `E` editar (`Ctrl+S` guarda, `Esc` cancela) · `L` biblioteca de guías · `I` índice de tarjetas · `A` controles de transparencia y tamaño · `Ctrl+V` pega el portapapeles como una guía nueva · `F5` recargar · `?` ayuda con todos los atajos.

Con el mouse: arrastrar el encabezado para mover, arrastrar `◢` para cambiar el tamaño, `Ctrl`+rueda para el tamaño de letra, `Alt`+rueda para la transparencia del fondo, `Alt+Shift`+rueda para la del texto, clic en el índice para saltar a una tarjeta, doble clic en el cronómetro para reiniciarlo.

### Teclados con AltGr (español latinoamericano, alemán, etc.)

Windows interpreta AltGr como `Ctrl+Alt`. Un atajo global `Ctrl+Alt+Q` impediría escribir `@` (que en estos teclados es `AltGr+Q`) en cualquier programa. Por eso Invisipal detecta cuándo una combinación `Ctrl+Alt+tecla` escribe un carácter en el teclado activo y, en ese caso, registra automáticamente `Ctrl+Alt+Shift+tecla` (por ejemplo `Ctrl+Alt+Shift+Q` para salir). La ayuda (`?`) muestra la combinación realmente vigente. Se controla con `avoid_altgr_conflicts` (por defecto `true`).

Si en la ayuda un atajo aparece como `(in use by another app)`, otro programa lo tiene reservado. Algunos drivers de gráficos Intel usan `Ctrl+Alt+flechas` para rotar la pantalla: desactivar esos atajos en el panel de Intel o cambiar el atajo en `config.json`.

## Ventana: transparencia, índice y posiciones

- **Transparencia del fondo y del texto por separado**: con el botón `◐` (o la tecla `A`) aparecen los controles de Fondo, Texto y Tamaño. También con `Ctrl+Alt+RePág/AvPág` (fondo), `Ctrl+Alt+Shift+→/←` (texto), `Alt`+rueda (fondo) y `Alt+Shift`+rueda (texto). Con el fondo en 0 % solo flotan las letras, con un borde oscuro fino tipo subtítulo.
- **Índice de tarjetas** a la izquierda: un clic en una tarjeta salta a ella. Se agranda o achica arrastrando el divisor, `Ctrl`+rueda cambia su letra, y se oculta o muestra con `◧`, `I` o `Ctrl+Alt+I`.
- **Posiciones en pantalla**: `Ctrl+Alt+Shift+Inicio` arriba a la izquierda, `+RePág` arriba a la derecha, `+Fin` abajo a la derecha, `+AvPág` abajo a la izquierda, `+↑` arriba al centro (debajo de la cámara, para leer mirando a cámara) y `+↓` abajo al centro. Respeta la barra de tareas y funciona en el monitor donde esté la ventana.

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

Atajos para crear guías: copiar un texto y apretar `Ctrl+V` en Invisipal lo convierte en una guía nueva; `L` abre la biblioteca; `E` abre el editor integrado. Además, cualquier editor externo (VS Code, Bloc de notas) sirve: Invisipal recarga el archivo solo cuando cambia. Ejemplo incluido: [`invisipal/examples/guia.txt`](invisipal/examples/guia.txt).

Todo (editor, biblioteca, ayuda) ocurre dentro de la misma ventana protegida a propósito: los popups o menús serían ventanas aparte, y esas sí se capturarían.

## Skill para Claude: de cualquier texto a tarjetas

El repo incluye un [skill para Claude](skills/invisipal-cards/SKILL.md) que arma las guías por vos. Se le pega un texto (notas desordenadas, un discurso, un mail, un documento) o se describe la reunión. Claude hace unas pocas preguntas (tipo de reunión; formato: tarjetas-recordatorio, guion de teleprompter, híbrido o checklist; idioma; largo), escribe la guía en el formato exacto que entiende Invisipal, la verifica con un script incluido y la guarda en `Documentos\Invisipal\guides\` o la deja lista para copiar y pegar con `Ctrl+V` en Invisipal.

Instalación:

- **Claude.ai o Claude escritorio**: bajar `invisipal-cards.skill` del [último release](https://github.com/nicoopal/invisipal/releases/latest) e ir a *Configuración → Capacidades → Skills → Subir skill*.
- **Claude Code**: copiar la carpeta `skills\invisipal-cards` a `%USERPROFILE%\.claude\skills\`.

Ejemplo de uso: *"armame las tarjetas de Invisipal para la call de mañana con estas notas: …"*.

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

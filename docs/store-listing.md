# Microsoft Store listing

Copy-paste material for Partner Center (*Apps and games → Invisipal*). Limits noted in brackets are the Store's. The package declares **English (en-us)** and **Spanish (es)**, so Partner Center asks for a listing in both.

## Submission settings

| Field | Value |
|---|---|
| Pricing | Free |
| Markets | All |
| Category | Productivity |
| Subcategory | (none) |
| Privacy policy URL | `https://github.com/nicoopal/invisipal/blob/main/PRIVACY.md` |
| Website | `https://github.com/nicoopal/invisipal` |
| Support contact | `https://github.com/nicoopal/invisipal/issues` |
| Copyright | © 2026 Nico Palermo |
| System requirements | Windows 10 version 2004 (build 19041) or newer, or Windows 11. Keyboard recommended. |
| Package | `Invisipal-<version>.msix` from the MSIX workflow artifact or `scripts\build-msix.ps1` |

### Age rating questionnaire (IARC)

Category: *All other app types*. Answer **No** to every content question: no violence, sex, drugs, gambling or profanity; no communication between users; no sharing of location or personal information; no purchases; no unrestricted web access. Expected rating: **3+ / Everyone**.

### Restricted capability: `runFullTrust`

Partner Center asks why the package needs it. Paste:

> Invisipal is a classic desktop (Win32) app packaged as MSIX. It needs full trust to register system-wide keyboard shortcuts (RegisterHotKey) that work while another app is in focus, to set its own window's display affinity (SetWindowDisplayAffinity) so it stays out of screen sharing, and to read and write the user's note files in Documents\Invisipal. It does not access the network.

### Notes for certification

Paste this so the reviewer knows what to expect:

> Invisipal shows the user's own notes in a small always-on-top window that is intentionally excluded from screen capture using the documented SetWindowDisplayAffinity(WDA_EXCLUDEFROMCAPTURE) API. This is the core feature: presenters can read their notes while sharing their entire screen in Teams, Zoom or Meet without the audience seeing them. Because of this, the window does not appear in screenshots or screen recordings taken by the reviewer; that is expected behavior, not a rendering bug. The green "● private" badge in the window header confirms the protection is active.
>
> How to test: launch Invisipal; an example guide opens. Press Ctrl+Alt+Right / Ctrl+Alt+Left to move between cards (global shortcuts, they work without focus), Ctrl+Alt+H to hide/show, and press "?" in the window for every shortcut. On Spanish/Latin American/German keyboards the quit shortcut becomes Ctrl+Alt+Shift+Q so it doesn't block typing "@". No account, network or sample data needed. The app stores its files in Documents\Invisipal.

## Store listing: English (en-us)

**Product name:** Invisipal

**Description** [max 10,000 characters]:

```text
Your notes, on your screen, invisible to everyone else.

Invisipal is a private teleprompter for meetings. It shows your talking points, agenda, script or cheat sheet in a small translucent window that stays on top of everything, and it is excluded from screen capture: when you share your entire screen in Microsoft Teams, Zoom or Google Meet, you can see Invisipal, but the people in the meeting can't.

ONE CARD AT A TIME
Paste or write your notes and Invisipal splits them into cards. A line with "---" starts a new card, or it splits by headings. You see one card at a time with a "3 / 10" counter, a preview of the next card's title and a card index on the side: click any card to jump to it.

MADE FOR THE MIDDLE OF A CALL
Global keyboard shortcuts work while your meeting app has focus: Ctrl+Alt+Right / Left for the next and previous card, Ctrl+Alt+Up / Down for text size, Ctrl+Alt+H to show or hide. Long cards scroll a page at a time before moving on, like a teleprompter. A built-in timer keeps you on schedule.

YOUR WINDOW, YOUR WAY
Set the background and the text transparency separately, down to only the letters floating over your slides. Snap the window to any corner, or to the top center, right under your webcam, so you read while looking at the camera. Hide it from the taskbar and Alt+Tab, or let clicks pass straight through it.

SIMPLE, PRIVATE FILES
Guides are plain text and Markdown files in Documents\Invisipal: edit them in the built-in editor or in any text editor and Invisipal reloads them automatically. Use bold, highlights, checklists, quotes and lists. One guide per meeting; switch between them with a shortcut.

PRIVATE BY DESIGN
No account, no internet connection, no telemetry. Your notes never leave your PC.

Requires Windows 10 version 2004 or newer, or Windows 11. Screen-capture exclusion protects against software screen sharing and screenshots, not against a camera pointed at your monitor. Please use Invisipal where personal notes are allowed.
```

**What's new in this version** [max 1,500 characters]:

```text
- Separate background and text transparency, down to text floating on its own.
- Card index on the left: click to jump to any card; resize or hide it.
- Shortcuts to snap the window to any corner or to the top center, under your webcam.
- New app icon.
```

**Product features** [up to 20, max 200 characters each]:

```text
Hidden from screen sharing in Teams, Zoom and Google Meet, and from screenshots
Shows your notes one card at a time with a "3 / 10" counter and a next-card preview
Card index: click any card to jump to it
Global shortcuts that work while your meeting app has focus
Teleprompter scrolling for long scripts
Separate background and text transparency
Snap to any corner or under your webcam
Plain text and Markdown guides with automatic reload
Built-in editor, guide library and meeting timer
No account, no internet, no telemetry
```

**Search terms** [up to 7]:

```text
teleprompter
meeting notes
speaker notes
screen sharing
cue cards
presentation
private notes
```

**Screenshots:** `docs/store/screenshot-1.png` to `screenshot-3.png` (1920 × 1080). **Store logo:** `docs/store/logo-300.png`.

## Store listing: Spanish (es)

**Product name:** Invisipal

**Description** [máximo 10.000 caracteres]:

```text
Tus notas en tu pantalla, invisibles para los demás.

Invisipal es un teleprompter privado para reuniones. Muestra tus puntos clave, agenda, guion o ayudamemoria en una ventana chica y translúcida que queda encima de todo, y está excluida de la captura de pantalla: cuando compartís la pantalla completa en Microsoft Teams, Zoom o Google Meet, vos ves Invisipal, pero los demás no.

UNA TARJETA A LA VEZ
Pegá o escribí tus notas e Invisipal las divide en tarjetas. Una línea con "---" empieza una tarjeta nueva, o divide por títulos. Ves una tarjeta a la vez con un contador "3 / 10", el título de la siguiente y un índice al costado: con un clic saltás a cualquier tarjeta.

HECHO PARA USAR EN PLENA LLAMADA
Atajos de teclado globales que funcionan aunque la app de la reunión tenga el foco: Ctrl+Alt+Derecha / Izquierda para la tarjeta siguiente y anterior, Ctrl+Alt+Arriba / Abajo para el tamaño de letra, Ctrl+Alt+H para mostrar u ocultar. Las tarjetas largas avanzan de a una página, como un teleprompter. Incluye un cronómetro.

TU VENTANA, A TU MANERA
Ajustá por separado la transparencia del fondo y la del texto, hasta dejar solo las letras flotando sobre tus diapositivas. Llevá la ventana a cualquier esquina o arriba al centro, justo debajo de la cámara, para leer mirando a cámara. Ocultala de la barra de tareas y de Alt+Tab, o dejá que los clics la atraviesen.

ARCHIVOS SIMPLES Y PRIVADOS
Las guías son archivos de texto y Markdown en Documentos\Invisipal: editalas en el editor incluido o en cualquier editor de texto e Invisipal las recarga sola. Usá negrita, resaltado, checklists, citas y listas. Una guía por reunión, y un atajo para cambiar entre ellas.

PRIVADA POR DISEÑO
Sin cuenta, sin conexión a internet, sin telemetría. Tus notas nunca salen de tu PC.

Requiere Windows 10 versión 2004 o posterior, o Windows 11. La exclusión de la captura protege frente a la pantalla compartida y las capturas por software, no frente a una cámara apuntando al monitor. Usá Invisipal donde estén permitidas las notas personales.
```

**Novedades de esta versión** [máximo 1.500 caracteres]:

```text
- Transparencia del fondo y del texto por separado, hasta dejar solo el texto flotando.
- Índice de tarjetas a la izquierda: clic para saltar a cualquier tarjeta; se puede agrandar u ocultar.
- Atajos para llevar la ventana a cualquier esquina o arriba al centro, debajo de la cámara.
- Ícono nuevo.
```

**Características** [hasta 20, máximo 200 caracteres cada una]:

```text
Invisible al compartir pantalla en Teams, Zoom y Google Meet, y en las capturas
Muestra tus notas de a una tarjeta con contador "3 / 10" y el título de la siguiente
Índice de tarjetas: un clic para saltar a cualquiera
Atajos globales que funcionan con la app de la reunión en primer plano
Desplazamiento tipo teleprompter para guiones largos
Transparencia del fondo y del texto por separado
Ubicá la ventana en cualquier esquina o debajo de la cámara
Guías en texto plano y Markdown con recarga automática
Editor, biblioteca de guías y cronómetro incluidos
Sin cuenta, sin internet, sin telemetría
```

**Términos de búsqueda** [hasta 7]:

```text
teleprompter
notas de reunión
apuntes
compartir pantalla
tarjetas
presentación
notas privadas
```

# Web oficial de viNiak

Web estática preparada para GitHub Pages o Hostinger.

## Publicar en GitHub Pages

1. Crea un repositorio público, por ejemplo `viniak-web`.
2. Sube todos los archivos de esta carpeta a la raíz del repositorio.
3. En GitHub abre `Settings > Pages`.
4. Selecciona `Deploy from a branch`, rama `main` y carpeta `/root`.
5. En `Custom domain`, introduce `viniak.es`.
6. Configura en Hostinger los registros DNS oficiales de GitHub Pages.

## Publicar en Hostinger

1. Entra en el Administrador de archivos de Hostinger.
2. Abre la carpeta `public_html` de `viniak.es`.
3. Sube a esa carpeta el contenido completo de este proyecto.
4. Comprueba que `index.html` queda directamente dentro de `public_html`.
5. Activa SSL/HTTPS desde hPanel.

## Archivos

- `index.html`: estructura y contenido.
- `styles.css`: diseño responsive.
- `script.js`: menú móvil, animaciones y año automático.
- `assets/viniak-logo.jpg`: imagen identificativa utilizada en la web.

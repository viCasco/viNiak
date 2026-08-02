const menuButton = document.querySelector('.menu-button');
const nav = document.querySelector('.main-nav');
menuButton?.addEventListener('click', () => {
  const open = nav.classList.toggle('open');
  menuButton.setAttribute('aria-expanded', String(open));
});
nav?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => {
  nav.classList.remove('open');
  menuButton?.setAttribute('aria-expanded', 'false');
}));

const observer = new IntersectionObserver(entries => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      observer.unobserve(entry.target);
    }
  });
}, { threshold: 0.12 });

document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
document.getElementById('year').textContent = new Date().getFullYear();

async function loadYouTubeVideos() {
  const container = document.querySelector("#youtube-videos");

  if (!container) {
    return;
  }

  try {
    const response = await fetch("./data/youtube-videos.json", {
      cache: "no-store",
    });

    if (!response.ok) {
      throw new Error(
        `No se pudo cargar el listado: HTTP ${response.status}`
      );
    }

    const data = await response.json();
    const videos = Array.isArray(data.videos) ? data.videos : [];

    container.replaceChildren();

    if (videos.length === 0) {
      const emptyMessage = document.createElement("p");
      emptyMessage.className = "youtube-status";
      emptyMessage.textContent = "Todavía no hay vídeos disponibles.";

      container.append(emptyMessage);
      return;
    }

    videos.forEach((video) => {
      const article = document.createElement("article");
      article.className = "youtube-card";

      const link = document.createElement("a");
      link.className = "youtube-card__link";
      link.href = video.url;
      link.target = "_blank";
      link.rel = "noopener noreferrer";
      link.setAttribute(
        "aria-label",
        `Ver ${video.title} en YouTube`
      );

      const imageWrapper = document.createElement("div");
      imageWrapper.className = "youtube-card__image-wrapper";

      const image = document.createElement("img");
      image.className = "youtube-card__image";
      image.src = video.thumbnail;
      image.alt = "";
      image.loading = "lazy";
      image.decoding = "async";

      const playIcon = document.createElement("span");
      playIcon.className = "youtube-card__play";
      playIcon.setAttribute("aria-hidden", "true");
      playIcon.textContent = "▶";

      const content = document.createElement("div");
      content.className = "youtube-card__content";

      const title = document.createElement("h3");
      title.className = "youtube-card__title";
      title.textContent = video.title;

      const date = document.createElement("time");
      date.className = "youtube-card__date";

      if (video.publishedAt) {
        const publicationDate = new Date(video.publishedAt);

        if (!Number.isNaN(publicationDate.getTime())) {
          date.dateTime = video.publishedAt;
          date.textContent = publicationDate.toLocaleDateString(
            "es-ES",
            {
              day: "numeric",
              month: "long",
              year: "numeric",
            }
          );
        }
      }

      imageWrapper.append(image, playIcon);
      content.append(title);

      if (date.textContent) {
        content.append(date);
      }

      link.append(imageWrapper, content);
      article.append(link);
      container.append(article);
    });
  } catch (error) {
    console.error("Error cargando YouTube:", error);

    container.replaceChildren();

    const errorMessage = document.createElement("p");
    errorMessage.className = "youtube-status";
    errorMessage.textContent =
      "No ha sido posible cargar los vídeos en este momento.";

    container.append(errorMessage);
  }
}

document.addEventListener("DOMContentLoaded", loadYouTubeVideos);
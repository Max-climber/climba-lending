import "./styles.css";
import { initAnalytics } from "./analytics";
import { initHeroVideo } from "./heroVideo";
import { applyStoreLinksFromQuery, initDownloadTracking } from "./storeLinks";

const counterId = Number(document.documentElement.dataset.ymCounter);

initAnalytics(counterId);
applyStoreLinksFromQuery();
initDownloadTracking(counterId);
initHeroVideo();

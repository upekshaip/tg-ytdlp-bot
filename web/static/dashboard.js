(() => {
    const statusChip = document.getElementById("dashboard-status");
    const translations = {
        en: {
            "header.title": "Bot statistics",
            "header.subtitle": "Online dashboard for monitoring Telegram bot activity.",
            "tabs.activity": "Activity",
            "tabs.users": "Users",
            "tabs.content": "Content",
            "tabs.moderation": "Moderation",
            "tabs.history": "History",
            "tabs.system": "System",
            "tabs.lists": "Lists",
            "history.title": "User History",
            "history.subtitle": "View download history for any user.",
            "status.online": "ONLINE",
            "status.updating": "UPDATING…",
            "cards.active.title": "Active users",
            "cards.active.subtitle": "Sessions during last {minutes} minutes.",
            "cards.active.count_label": "Now",
            "cards.top_downloaders.title": "Top downloaders",
            "cards.top_downloaders.subtitle": "Pick a period for the ranking.",
            "cards.channel.title": "Channel activity ({hours}h)",
            "cards.channel.subtitle": "Join and leave events in the log channel.",
            "cards.suspicious.title": "Suspicious users",
            "cards.suspicious.subtitle": "Users with the smallest breaks between downloads.",
            "cards.countries.title": "Top countries",
            "cards.countries.subtitle": "Detected via language/flag.",
            "cards.gender.title": "Gender & age",
            "cards.gender.subtitle": "Groups based on heuristics.",
            "cards.gender.gender_label": "Gender",
            "cards.gender.age_label": "Age",
            "cards.nsfw_users.title": "NSFW users",
            "cards.nsfw_users.subtitle": "Most frequent NSFW downloads.",
            "cards.playlists.title": "Playlist lovers",
            "cards.playlists.subtitle": "Users who request playlists most.",
            "cards.power.title": "Power users",
            "cards.power.subtitle": "At least 10 URLs every day during 7 consecutive days.",
            "cards.domains.title": "Top domains",
            "cards.domains.subtitle": "Where links come from.",
            "cards.nsfw_domains.title": "NSFW sites",
            "cards.nsfw_domains.subtitle": "Most requested NSFW domains.",
            "cards.blocked.title": "Banned users",
            "cards.blocked.subtitle": "Use ✅ to unblock.",
            "filters.today": "Today",
            "filters.week": "Week",
            "filters.month": "Month",
            "filters.all": "All time",
            "misc.empty": "No data for the selected period",
            "buttons.show_all": "Show all",
            "buttons.collapse": "Collapse",
            "buttons.theme_dark": "Dark theme",
            "buttons.theme_light": "Light theme",
            "meta.no_username": "no username",
            "meta.id_label": "ID",
            "meta.days": "{value} d",
            "modals.block_confirm": "Block user {id}?",
            "modals.unblock_confirm": "Unblock user {id}?",
            "time.just_now": "just now",
            "time.minutes": "{value} min ago",
            "time.hours": "{value} h ago",
            "time.days": "{value} d ago",
            "system.metrics": "System Metrics",
            "system.versions": "Package Versions",
            "system.config": "Configuration",
            "system.ip_rotate": "Rotate IP",
            "system.restart": "Restart Service",
            "system.cleanup": "Cleanup User Files",
            "system.update_engines": "Update Engines",
            "lists.stats": "File Statistics",
            "lists.domains": "Domain Lists",
            "lists.update": "Update Lists",
            "power.min_urls": "Min URLs per day:",
            "power.days": "Days:",
            "power.apply": "Apply",
            "demographics.title": "Demographics & Countries",
            "demographics.subtitle": "User statistics by country, gender, and registration date.",
            "demographics.countries": "Top Countries",
            "demographics.gender": "Gender",
            "demographics.age": "Registered",
            "buttons.logout": "Logout",
            "buttons.save": "Save",
            "buttons.add": "Add",
            "buttons.view_media": "Media info",
            "buttons.view_user": "User info",
            "modals.user_title": "User details",
            "modals.media_title": "Media details",
            "labels.username": "Username",
            "labels.user_id": "User ID",
            "labels.country": "Country",
            "labels.gender": "Gender",
            "labels.age": "Registered at",
            "labels.last_event": "Last activity",
            "labels.url": "URL",
            "labels.progress": "Progress",
            "labels.size": "Size",
            "labels.downloaded": "Downloaded",
            "labels.quality": "Quality",
            "labels.resolution": "Resolution",
            "labels.duration": "Duration",
            "labels.speed": "Speed",
            "labels.eta": "ETA",
            "labels.format": "Format",
            "labels.domain": "Domain",
            "labels.max_gap": "Break: {value}",
            "labels.downloads": "{value} downloads",
            "misc.no_url": "No URL",
            "misc.no_metadata": "No additional metadata",
            "misc.unknown": "unknown"
        },
        ru: {
            "header.title": "Статистика бота",
            "header.subtitle": "Онлайн-дашборд для мониторинга активности Telegram-бота.",
            "tabs.activity": "Активность",
            "tabs.users": "Пользователи",
            "tabs.content": "Контент",
            "tabs.moderation": "Модерация",
            "tabs.history": "История",
            "tabs.system": "Система",
            "tabs.lists": "Списки",
            "history.title": "История пользователя",
            "history.subtitle": "Просмотр истории загрузок любого пользователя.",
            "status.online": "ОНЛАЙН",
            "status.updating": "ОБНОВЛЕНИЕ…",
            "cards.active.title": "Активные пользователи",
            "cards.active.subtitle": "Сессии за последние {minutes} минут.",
            "cards.active.count_label": "Сейчас",
            "cards.top_downloaders.title": "Топ загрузчиков",
            "cards.top_downloaders.subtitle": "Выберите период для рейтинга.",
            "cards.channel.title": "Действия в канале ({hours}ч)",
            "cards.channel.subtitle": "Вступления и выходы в лог-канале.",
            "cards.suspicious.title": "Подозрительные пользователи",
            "cards.suspicious.subtitle": "Минимальные перерывы между загрузками.",
            "cards.countries.title": "Топ стран",
            "cards.countries.subtitle": "Определение по языку/флагу.",
            "cards.gender.title": "Пол и возраст",
            "cards.gender.subtitle": "Группы по эвристикам.",
            "cards.gender.gender_label": "Пол",
            "cards.gender.age_label": "Возраст",
            "cards.nsfw_users.title": "NSFW пользователи",
            "cards.nsfw_users.subtitle": "Чаще всего качают NSFW.",
            "cards.playlists.title": "Любители плейлистов",
            "cards.playlists.subtitle": "Пользователи, которые чаще всего просят плейлисты.",
            "cards.power.title": "Постоянные хардкорщики",
            "cards.power.subtitle": "Как минимум 7 дней подряд по 10+ ссылок.",
            "cards.domains.title": "Топ доменов",
            "cards.domains.subtitle": "Источники ссылок.",
            "cards.nsfw_domains.title": "NSFW сайты",
            "cards.nsfw_domains.subtitle": "Самые популярные NSFW домены.",
            "cards.blocked.title": "Забаненные пользователи",
            "cards.blocked.subtitle": "Кнопка ✅ снимает бан.",
            "filters.today": "Сегодня",
            "filters.week": "Неделя",
            "filters.month": "Месяц",
            "filters.all": "За всё время",
            "misc.empty": "Нет данных за выбранный период",
            "buttons.show_all": "Показать все",
            "buttons.collapse": "Свернуть",
            "buttons.theme_dark": "Тёмная тема",
            "buttons.theme_light": "Светлая тема",
            "meta.no_username": "без ника",
            "meta.id_label": "ID",
            "meta.days": "{value} дн",
            "modals.block_confirm": "Заблокировать пользователя {id}?",
            "modals.unblock_confirm": "Разблокировать пользователя {id}?",
            "time.just_now": "только что",
            "time.minutes": "{value} мин назад",
            "time.hours": "{value} ч назад",
            "time.days": "{value} дн назад",
            "system.metrics": "Метрики системы",
            "system.versions": "Версии пакетов",
            "system.config": "Конфигурация",
            "system.ip_rotate": "Сменить IP",
            "system.restart": "Перезапустить сервис",
            "system.cleanup": "Очистить файлы пользователей",
            "system.update_engines": "Обновить движки",
            "lists.stats": "Статистика файлов",
            "lists.domains": "Списки доменов",
            "lists.update": "Обновить списки",
            "power.min_urls": "Мин. URL в день:",
            "power.days": "Дней:",
            "power.apply": "Применить",
            "demographics.title": "Демография и страны",
            "demographics.subtitle": "Статистика пользователей по странам, полу и дате регистрации.",
            "demographics.countries": "Топ стран",
            "demographics.gender": "Пол",
            "demographics.age": "Регистрация",
            "buttons.logout": "Выход",
            "buttons.save": "Сохранить",
            "buttons.add": "Добавить",
            "buttons.view_media": "Информация о видео",
            "buttons.view_user": "Профиль пользователя",
            "modals.user_title": "Данные пользователя",
            "modals.media_title": "Данные по медиа",
            "labels.username": "Имя/ник",
            "labels.user_id": "ID пользователя",
            "labels.country": "Страна",
            "labels.gender": "Пол",
            "labels.age": "Дата регистрации",
            "labels.last_event": "Последняя активность",
            "labels.url": "Ссылка",
            "labels.progress": "Прогресс",
            "labels.size": "Размер",
            "labels.downloaded": "Скачано",
            "labels.quality": "Качество",
            "labels.resolution": "Разрешение",
            "labels.duration": "Длительность",
            "labels.speed": "Скорость",
            "labels.eta": "Осталось",
            "labels.format": "Формат",
            "labels.domain": "Домен",
            "labels.max_gap": "Перерыв: {value}",
            "labels.downloads": "{value} загрузок",
            "misc.no_url": "Нет ссылки",
            "misc.no_metadata": "Дополнительные данные отсутствуют",
            "misc.unknown": "неизвестно"
        }
    };

    translations.hi = {
        ...translations.en,
        "header.title": "बॉट आँकड़े",
        "header.subtitle": "टेलीग्राम बॉट की गतिविधि पर नज़र रखने वाला डैशबोर्ड.",
        "tabs.activity": "गतिविधि",
        "tabs.users": "उपयोगकर्ता",
        "tabs.content": "सामग्री",
        "tabs.moderation": "मॉडरेशन",
        "tabs.history": "इतिहास",
        "tabs.system": "सिस्टम",
        "tabs.lists": "सूचियाँ",
        "history.title": "उपयोगकर्ता इतिहास",
        "history.subtitle": "किसी भी उपयोगकर्ता की डाउनलोड इतिहास देखें।",
        "status.online": "ऑनलाइन",
        "status.updating": "अपडेट हो रहा है…",
        "cards.active.title": "सक्रिय उपयोगकर्ता",
        "cards.active.subtitle": "पिछले {minutes} मिनट की सत्र जानकारी.",
        "cards.active.count_label": "अभी",
        "cards.suspicious.title": "संदिग्ध उपयोगकर्ता",
        "cards.suspicious.subtitle": "जिनके डाउनलोड के बीच बहुत कम अंतर है.",
        "cards.top_downloaders.title": "शीर्ष डाउनलोडर",
        "cards.channel.title": "चैनल गतिविधि ({hours}घं)",
        "cards.channel.subtitle": "लॉग चैनल में शामिल/छोड़ने की घटनाएँ.",
        "buttons.theme_dark": "डार्क थीम",
        "buttons.theme_light": "लाइट थीम",
        "misc.empty": "चयनित अवधि के लिए डेटा नहीं",
        "labels.max_gap": "अंतर: {value}",
        "labels.downloads": "{value} डाउनलोड",
    };

    translations.ar = {
        ...translations.en,
        "header.title": "إحصائيات البوت",
        "header.subtitle": "لوحة لمراقبة نشاط بوت تيليغرام.",
        "tabs.activity": "النشاط",
        "tabs.users": "المستخدمون",
        "tabs.content": "المحتوى",
        "tabs.moderation": "الإشراف",
        "tabs.history": "السجل",
        "tabs.system": "النظام",
        "tabs.lists": "القوائم",
        "history.title": "سجل المستخدم",
        "history.subtitle": "عرض سجل التنزيلات لأي مستخدم.",
        "status.online": "متصل",
        "status.updating": "يتم التحديث…",
        "cards.active.title": "المستخدمون النشطون",
        "cards.active.subtitle": "جلسات خلال آخر {minutes} دقيقة.",
        "cards.active.count_label": "الآن",
        "cards.suspicious.title": "مستخدمون مشبوهون",
        "cards.suspicious.subtitle": "أقصر فترات التوقف بين التنزيلات.",
        "cards.top_downloaders.title": "الأكثر تحميلًا",
        "cards.channel.title": "نشاط القناة ({hours}س)",
        "cards.channel.subtitle": "أحداث الانضمام والمغادرة في قناة السجل.",
        "buttons.theme_dark": "الوضع الداكن",
        "buttons.theme_light": "الوضع الفاتح",
        "misc.empty": "لا توجد بيانات للفترة المحددة",
        "labels.max_gap": "الفاصل: {value}",
        "labels.downloads": "{value} تنزيل",
    };

    const selectors = {};
    let currentLang = localStorage.getItem("dashboardLang") || "en";
    let statusMode = "online";
    let emptyStateText = translations.en["misc.empty"];
    let modalRoot;
    let modalTitleEl;
    let modalBodyEl;
    let themeToggleBtn;
    let currentTheme = localStorage.getItem("dashboardTheme") || "dark";

    const endpoints = {
        activeUsers: (minutes = 15, limit = 100) =>
            `/api/active-users?limit=${limit}&minutes=${minutes}`,
        topDownloaders: (period = "today", limit = 100) => `/api/top-downloaders?period=${period}&limit=${limit}`,
        countries: (period = "today", limit = 50) => `/api/top-countries?period=${period}&limit=${limit}`,
        gender: (period = "today") => `/api/gender-stats?period=${period}`,
        age: (period = "today") => `/api/age-stats?period=${period}`,
        domains: (period = "today", limit = 50) => `/api/top-domains?period=${period}&limit=${limit}`,
        nsfwUsers: (limit = 100) => `/api/top-nsfw-users?limit=${limit}`,
        nsfwDomains: (limit = 50) => `/api/top-nsfw-domains?limit=${limit}`,
        playlistUsers: (limit = 100) => `/api/top-playlist-users?limit=${limit}`,
        powerUsers: (minUrls = 10, days = 7, limit = 50) => `/api/power-users?min_urls=${minUrls}&days=${days}&limit=${limit}`,
        blockedUsers: (limit = 200) => `/api/blocked-users?limit=${limit}`,
        channelEvents: (hours = 48, limit = 200) => `/api/channel-events?hours=${hours}&limit=${limit}`,
        suspiciousUsers: (period = "today", limit = 50) => `/api/suspicious-users?period=${period}&limit=${limit}`,
        userHistory: (userId, period = "all", limit = 100) => `/api/user-history?user_id=${userId}&period=${period}&limit=${limit}`,
    };

    function t(key) {
        return translations[currentLang][key] ?? translations.en[key] ?? key;
    }

    function replacePlaceholders(text, replacements = {}) {
        return Object.entries(replacements).reduce((acc, [token, value]) => acc.replaceAll(`{${token}}`, value), text);
    }

    function updateStatusText() {
        const key = statusMode === "loading" ? "status.updating" : "status.online";
        statusChip.textContent = t(key);
    }

    function setStatus(mode) {
        statusMode = mode;
        updateStatusText();
    }

    async function fetchJSON(url, options = {}) {
        setStatus("loading");
        try {
            const response = await fetch(url, options);
            if (!response.ok) {
                const text = await response.text();
                throw new Error(text || "Request failed");
            }
            const text = await response.text();
            if (!text) return {};
            try {
                return JSON.parse(text);
            } catch (err) {
                throw new Error(`Invalid JSON response: ${text.substring(0, 120)}`);
            }
        } finally {
            setStatus("online");
        }
    }

    function formatUserMeta(item) {
        const username = item.username ? `@${item.username}` : t("meta.no_username");
        return `${username} • ${t("meta.id_label")}: ${item.user_id}`;
    }

    function relativeTime(ts) {
        if (!ts) return "";
        const diff = Date.now() - ts * 1000;
        const minutes = Math.floor(diff / 60000);
        if (minutes < 1) return t("time.just_now");
        if (minutes < 60) return replacePlaceholders(t("time.minutes"), { value: minutes });
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return replacePlaceholders(t("time.hours"), { value: hours });
        const days = Math.floor(hours / 24);
        return replacePlaceholders(t("time.days"), { value: days });
    }

    function formatBytes(bytes) {
        if (bytes === undefined || bytes === null) {
            return t("misc.unknown");
        }
        if (bytes === 0) return "0 B";
        const units = ["B", "KB", "MB", "GB", "TB"];
        const idx = Math.floor(Math.log(bytes) / Math.log(1024));
        const value = bytes / Math.pow(1024, idx);
        return `${value.toFixed(value >= 10 ? 0 : 1)} ${units[idx]}`;
    }

    function formatDuration(seconds) {
        if (!seconds && seconds !== 0) return t("misc.unknown");
        const secs = Math.max(0, Math.floor(seconds));
        const hours = Math.floor(secs / 3600);
        const minutes = Math.floor((secs % 3600) / 60);
        const remaining = secs % 60;
        if (hours) {
            return `${hours}h ${minutes}m`;
        }
        return `${minutes}m ${remaining}s`;
    }

    function formatGapLabel(seconds) {
        if (seconds === undefined || seconds === null) {
            return t("misc.unknown");
        }
        const secs = Math.max(0, Math.round(seconds));
        if (secs < 60) {
            return `${secs}s`;
        }
        const minutes = Math.floor(secs / 60);
        if (minutes < 60) {
            return `${minutes}m`;
        }
        const hours = Math.floor(minutes / 60);
        if (hours < 24) {
            const mins = minutes % 60;
            return mins ? `${hours}h ${mins}m` : `${hours}h`;
        }
        const days = Math.floor(hours / 24);
        const remHours = hours % 24;
        return remHours ? `${days}d ${remHours}h` : `${days}d`;
    }

    function formatSpeed(bytesPerSecond) {
        if (!bytesPerSecond) return t("misc.unknown");
        return `${formatBytes(bytesPerSecond)}/s`;
    }

    function truncate(text, limit = 42) {
        if (!text) return "";
        return text.length > limit ? `${text.slice(0, limit - 1)}…` : text;
    }

    function prettifyUrl(url) {
        if (!url) return t("misc.no_url");
        try {
            const parsed = new URL(url);
            return `${parsed.hostname}${parsed.pathname !== "/" ? parsed.pathname : ""}`;
        } catch (err) {
            return truncate(url, 32);
        }
    }

    function renderDetailsList(rows) {
        const filtered = rows.filter((row) => row.value);
        if (!filtered.length) {
            return `<p class="empty-state">${t("misc.no_metadata")}</p>`;
        }
        return `
            <dl class="details-list">
                ${filtered
                    .map(
                        (row) => `
                        <dt>${row.label}</dt>
                        <dd>${row.value}</dd>
                    `
                    )
                    .join("")}
            </dl>
        `;
    }

    function openModal(title, html) {
        if (!modalRoot) return;
        modalTitleEl.textContent = title;
        modalBodyEl.innerHTML = html;
        modalRoot.classList.remove("hidden");
        modalRoot.classList.add("visible");
    }

    function closeModal() {
        if (!modalRoot) return;
        modalRoot.classList.remove("visible");
        modalRoot.classList.add("hidden");
    }

    function updateThemeToggleLabel() {
        if (!themeToggleBtn) {
            return;
        }
        themeToggleBtn.textContent = t(currentTheme === "light" ? "buttons.theme_dark" : "buttons.theme_light");
    }

    function applyTheme(theme) {
        currentTheme = theme === "light" ? "light" : "dark";
        document.body.classList.toggle("theme-light", currentTheme === "light");
        localStorage.setItem("dashboardTheme", currentTheme);
        updateThemeToggleLabel();
    }

    function setupThemeToggle() {
        if (!themeToggleBtn) return;
        themeToggleBtn.addEventListener("click", () => {
            const nextTheme = currentTheme === "dark" ? "light" : "dark";
            applyTheme(nextTheme);
        });
        applyTheme(currentTheme);
    }

    function setListData(container, items, renderer) {
        container.__items = items || [];
        container.__renderer = renderer;
        updateListView(container);
    }

    function updateListView(container) {
        const items = container.__items || [];
        const button = document.querySelector(`[data-expand-button="${container.id}"]`);
        if (!items.length) {
            container.innerHTML = `<div class="empty-state">${emptyStateText}</div>`;
            if (button) {
                button.style.display = "none";
            }
            return;
        }
        const limit = parseInt(container.dataset.expandLimit || "10", 10);
        const expanded = container.dataset.expanded === "true";
        const list = expanded ? items : items.slice(0, limit);
        container.innerHTML = "";
        list.forEach((item) => container.__renderer(item, container));
        if (button) {
            const hidden = items.length <= limit;
            button.style.display = hidden ? "none" : "inline-flex";
            button.textContent = expanded ? t("buttons.collapse") : t("buttons.show_all");
        }
    }

    let currentHistoryUserId = null;

    async function loadHistoryUsers() {
        // Получаем всех пользователей из топов для поиска
        const [topUsers, suspiciousUsers] = await Promise.all([
            fetchJSON(endpoints.topDownloaders("all", 500)),
            fetchJSON(endpoints.suspiciousUsers("all", 500)),
        ]);
        
        // Объединяем и убираем дубликаты
        const userMap = new Map();
        [...(topUsers || []), ...(suspiciousUsers || [])].forEach(user => {
            if (user.user_id && !userMap.has(user.user_id)) {
                userMap.set(user.user_id, user);
            }
        });
        
        const allUsers = Array.from(userMap.values());
        const container = document.getElementById("history-users-list");
        const searchInput = document.getElementById("history-search");
        
        const filterUsers = (query) => {
            if (!query) {
                return allUsers.slice(0, 50); // Показываем первые 50 без поиска
            }
            const lowerQuery = query.toLowerCase();
            return allUsers.filter(user => 
                String(user.user_id).includes(lowerQuery) ||
                (user.name || "").toLowerCase().includes(lowerQuery) ||
                (user.username || "").toLowerCase().includes(lowerQuery)
            ).slice(0, 50);
        };
        
        const renderUsers = (users) => {
            container.innerHTML = "";
            if (users.length === 0) {
                container.innerHTML = `<div class="empty-state">${emptyStateText}</div>`;
                return;
            }
            users.forEach(user => {
                const row = createUserRow(user, {
                    onRowClick: () => {
                        currentHistoryUserId = user.user_id;
                        loadUserHistory(user.user_id);
                    }
                });
                if (row) {
                    row.dataset.userId = user.user_id;
                    container.appendChild(row);
                }
            });
        };
        
        if (searchInput) {
            searchInput.addEventListener("input", (e) => {
                const filtered = filterUsers(e.target.value);
                renderUsers(filtered);
            });
        }
        
        renderUsers(filterUsers(""));
    }

    async function loadUserHistory(userId) {
        // Получаем имя пользователя
        const userRow = Array.from(document.getElementById("history-users-list").children).find(
            row => row.dataset.userId === String(userId)
        );
        const userName = userRow ? (userRow.querySelector(".title")?.textContent || `User ${userId}`) : `User ${userId}`;
        
        // Загружаем все данные (без ограничения по периоду для фильтрации на клиенте)
        const allData = await fetchJSON(endpoints.userHistory(userId, "all", 1000));
        
        if (!allData || allData.length === 0) {
            openModal(
                `History: ${userName}`,
                `<div class="empty-state">No downloads found for this user</div>`
            );
            return;
        }
        
        // Создаем модальное окно с поиском и фильтрацией
        let currentPeriod = "all";
        let currentSearch = "";
        let filteredData = [...allData];
        
        const renderHistory = () => {
            // Фильтрация по периоду
            let periodFiltered = filteredData;
            if (currentPeriod !== "all") {
                const now = Date.now();
                const periodMap = {
                    "today": 24 * 60 * 60 * 1000,
                    "week": 7 * 24 * 60 * 60 * 1000,
                    "month": 30 * 24 * 60 * 60 * 1000,
                };
                const threshold = now - periodMap[currentPeriod];
                periodFiltered = filteredData.filter(item => item.timestamp * 1000 >= threshold);
            }
            
            // Поиск по URL и названию
            let searchFiltered = periodFiltered;
            if (currentSearch) {
                const searchLower = currentSearch.toLowerCase();
                searchFiltered = periodFiltered.filter(item => 
                    (item.url || "").toLowerCase().includes(searchLower) ||
                    (item.title || "").toLowerCase().includes(searchLower) ||
                    (item.domain || "").toLowerCase().includes(searchLower)
                );
            }
            
            // Сортировка по времени (новые сначала)
            searchFiltered.sort((a, b) => b.timestamp - a.timestamp);
            
            const container = document.getElementById("history-modal-list");
            if (!container) return;
            
            if (searchFiltered.length === 0) {
                container.innerHTML = `<div class="empty-state">No downloads found matching your filters</div>`;
                return;
            }
            
            container.innerHTML = "";
            searchFiltered.forEach(item => {
                const row = document.createElement("div");
                row.className = "list-row";
                const date = new Date(item.timestamp * 1000).toLocaleString();
                const badges = [];
                if (item.is_nsfw) badges.push('<span class="badge" style="background: #ef4444; color: white;">NSFW</span>');
                if (item.is_playlist) badges.push('<span class="badge" style="background: #3b82f6; color: white;">Playlist</span>');
                
                const title = item.title || item.url || "No title";
                const url = item.url || "";
                const domain = item.domain || "unknown domain";
                
                row.innerHTML = `
                    <div class="list-row__info">
                        <span class="flag">•</span>
                        <div style="flex: 1; min-width: 0;">
                            <span class="title" style="display: block; margin-bottom: 0.25rem;">${title}</span>
                            <div class="meta">${date} • ${domain}</div>
                            ${url ? `<div class="meta" style="font-size: 0.75rem; margin-top: 0.25rem; word-break: break-all;">${url}</div>` : ""}
                        </div>
                    </div>
                    <div class="list-row__actions">
                        ${badges.join("")}
                    </div>
                `;
                container.appendChild(row);
            });
            
            // Обновляем счетчик
            const counter = document.getElementById("history-modal-count");
            if (counter) {
                counter.textContent = `Showing ${searchFiltered.length} of ${allData.length} items`;
            }
        };
        
        const modalHtml = `
            <div style="display: flex; flex-direction: column; gap: 1rem;">
                <div style="display: flex; gap: 0.5rem; flex-wrap: wrap; align-items: center;">
                    <input 
                        type="text" 
                        id="history-modal-search" 
                        class="search-input" 
                        placeholder="Search by URL, title, or domain..." 
                        style="flex: 1; min-width: 200px;"
                    >
                    <select id="history-modal-period" class="period-select">
                        <option value="all">All time</option>
                        <option value="today">Today</option>
                        <option value="week">Week</option>
                        <option value="month">Month</option>
                    </select>
                </div>
                <div id="history-modal-count" class="metric-label" style="font-size: 0.85rem;">
                    Showing ${allData.length} of ${allData.length} items
                </div>
                <div id="history-modal-list" class="list" style="max-height: 60vh; overflow-y: auto;"></div>
            </div>
        `;
        
        openModal(`History: ${userName}`, modalHtml);
        
        // Настраиваем обработчики событий
        setTimeout(() => {
            const searchInput = document.getElementById("history-modal-search");
            const periodSelect = document.getElementById("history-modal-period");
            
            if (searchInput) {
                searchInput.addEventListener("input", (e) => {
                    currentSearch = e.target.value;
                    renderHistory();
                });
            }
            
            if (periodSelect) {
                periodSelect.addEventListener("change", (e) => {
                    currentPeriod = e.target.value;
                    renderHistory();
                });
            }
            
            // Первоначальная отрисовка
            renderHistory();
        }, 100);
    }

    function createUserRow(item, options = {}) {
        const template = document.getElementById("user-row-template");
        const node = template.content.firstElementChild.cloneNode(true);
        const flag = node.querySelector("[data-flag]");
        const nameEl = node.querySelector("[data-name]");
        const metaEl = node.querySelector("[data-meta]");
        const extraEl = node.querySelector("[data-extra]");
        const button = node.querySelector("[data-block]");

        flag.textContent = item.flag || "🏳";
        
        // Добавляем ссылки на профили
        const nameText = item.name || `${t("meta.id_label")} ${item.user_id}`;
        if (item.username) {
            nameEl.innerHTML = `<a href="https://t.me/${item.username}" target="_blank" style="color: #38bdf8; text-decoration: none;">${nameText}</a>`;
        } else {
            nameEl.innerHTML = `<a href="tg://user?id=${item.user_id}" style="color: #38bdf8; text-decoration: none;">${nameText}</a>`;
        }
        
        // Добавляем ссылку на ID если есть username
        const metaText = options.meta ? options.meta(item) : formatUserMeta(item);
        if (item.username && item.user_id) {
            metaEl.innerHTML = `${metaText} • <a href="tg://user?id=${item.user_id}" style="color: #94a3b8; text-decoration: none; font-size: 0.85rem;">ID: ${item.user_id}</a>`;
        } else {
            metaEl.textContent = metaText;
        }
        const extraContent = options.extra ? options.extra(item) : "";
        if (typeof extraContent === "string") {
            extraEl.innerHTML = extraContent;
        } else if (extraContent instanceof HTMLElement) {
            extraEl.innerHTML = "";
            extraEl.appendChild(extraContent);
        } else {
            extraEl.textContent = "";
        }
        if (options.hideButton) {
            button.remove();
        } else {
            button.textContent = options.unblock ? "✅" : "❌";
            button.addEventListener("click", (event) => {
                event.stopPropagation();
                if (options.unblock) {
                    unblockUser(item.user_id);
                } else {
                    blockUser(item.user_id);
                }
            });
        }
        if (typeof options.onRowClick === "function") {
            node.classList.add("interactive");
            node.addEventListener("click", (event) => {
                if (event.target.closest("[data-block]") || event.target.classList.contains("chip-button")) {
                    return;
                }
                options.onRowClick(event);
            });
        }
        if (typeof options.afterRender === "function") {
            options.afterRender(node);
        }
        return node;
    }

    function buildMediaRows(item) {
        const metadata = item.metadata || {};
        const totalBytes = metadata.total_bytes || metadata.filesize;
        return [
            {
                label: t("labels.url"),
                value: item.url ? `<a href="${item.url}" target="_blank">${prettifyUrl(item.url)}</a>` : null,
            },
            { label: t("labels.domain"), value: metadata.domain || (item.url ? prettifyUrl(item.url) : null) },
            { label: t("labels.progress"), value: typeof item.progress === "number" ? `${item.progress.toFixed(1)}%` : t("misc.unknown") },
            { label: t("labels.size"), value: totalBytes ? formatBytes(totalBytes) : null },
            {
                label: t("labels.downloaded"),
                value: metadata.downloaded_bytes
                    ? `${formatBytes(metadata.downloaded_bytes)}${totalBytes ? ` / ${formatBytes(totalBytes)}` : ""}`
                    : null,
            },
            { label: t("labels.duration"), value: metadata.duration ? formatDuration(metadata.duration) : null },
            { label: t("labels.resolution"), value: metadata.resolution || null },
            { label: t("labels.quality"), value: metadata.quality || null },
            { label: t("labels.format"), value: metadata.ext || null },
            { label: t("labels.speed"), value: metadata.speed ? formatSpeed(metadata.speed) : null },
            { label: t("labels.eta"), value: metadata.eta ? formatDuration(metadata.eta) : null },
        ];
    }

    function showUserDetailsModal(item) {
        const usernameValue = item.username
            ? `<a href="https://t.me/${item.username}" target="_blank">${`@${item.username}`}</a>`
            : t("meta.no_username");
        const registeredValue = item.first_seen_ts
            ? new Date(item.first_seen_ts * 1000).toLocaleString()
            : t("misc.unknown");
        const userRows = [
            { label: t("labels.username"), value: usernameValue },
            { label: t("labels.user_id"), value: item.user_id },
            { label: t("labels.country"), value: item.flag ? `${item.flag} ${item.country_code || ""}` : t("misc.unknown") },
            { label: t("labels.gender"), value: item.gender || t("misc.unknown") },
            { label: t("labels.age"), value: registeredValue },
            { label: t("labels.progress"), value: typeof item.progress === "number" ? `${item.progress.toFixed(1)}%` : t("misc.unknown") },
            { label: t("labels.last_event"), value: item.last_event_ts ? new Date(item.last_event_ts * 1000).toLocaleString() : t("misc.unknown") },
        ];
        const mediaRows = buildMediaRows(item);
        const sections = [
            `<h4>${t("modals.user_title")}</h4>`,
            renderDetailsList(userRows),
            `<h4 style="margin-top:1.5rem;">${t("modals.media_title")}</h4>`,
            renderDetailsList(mediaRows),
        ].join("");
        openModal(t("modals.user_title"), sections);
    }

    function showMediaDetailsModal(item) {
        const rows = buildMediaRows(item);
        openModal(t("modals.media_title"), renderDetailsList(rows));
    }

    async function blockUser(userId) {
        if (!confirm(replacePlaceholders(t("modals.block_confirm"), { id: userId }))) {
            return;
        }
        await fetch("/api/block-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId }),
        });
        refreshModeration();
    }

    async function unblockUser(userId) {
        if (!confirm(replacePlaceholders(t("modals.unblock_confirm"), { id: userId }))) {
            return;
        }
        await fetch("/api/unblock-user", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: userId }),
        });
        refreshModeration();
    }

    function renderSimpleList(container, items, formatter, icon, showBadge = true) {
        if (!items || !items.length) {
            container.innerHTML = `<div class="empty-state">${emptyStateText}</div>`;
            container.__items = [];
            return;
        }
        container.__items = items; // Сохраняем для поиска
        container.innerHTML = "";
        items.forEach((item) => {
            const row = document.createElement("div");
            row.className = "list-row";
            const badgeHtml = showBadge ? `<div class="badge">${item.count ?? ""}</div>` : "";
            row.innerHTML = `
                <div class="list-row__info">
                    <span class="flag">${icon || "•"}</span>
                    <div>
                        <span class="title">${formatter(item)}</span>
                    </div>
                </div>
                ${badgeHtml}
            `;
            container.appendChild(row);
        });
    }

    function buildActiveMeta(item) {
        let meta = `${formatUserMeta(item)}`;
        if (item.url) {
            meta += ` • ${prettifyUrl(item.url)}`;
        }
        if (item.title) {
            meta += ` • ${truncate(item.title, 60)}`;
        }
        return meta;
    }

    function buildProgressDisplay(item) {
        if (typeof item.progress === "number") {
            const progressPercent = Math.max(0, Math.min(100, item.progress));
            return `
                <div style="display:flex; align-items:center; gap:0.5rem;">
                    <div style="width:120px; height:10px; background:rgba(148,163,184,0.2); border-radius:5px; overflow:hidden;">
                        <div style="width:${progressPercent}%; height:100%; background:linear-gradient(120deg,#22d3ee,#a855f7); transition:width 0.3s;"></div>
                    </div>
                    <span style="font-size:0.85rem; color:#38bdf8; font-weight:600; min-width:45px;">${progressPercent.toFixed(1)}%</span>
                </div>
            `;
        }
        return relativeTime(item.last_event_ts);
    }

    async function loadActiveUsers() {
        const minutes = selectors.activePeriod
            ? Number(selectors.activePeriod.value || selectors.activePeriod.dataset.defaultMinutes || 15)
            : 15;
        const data = await fetchJSON(endpoints.activeUsers(minutes || 15));
        const container = document.getElementById("active-users-list");
        const items = data.items || [];
        if (selectors.activeCount) {
            selectors.activeCount.textContent = data.total ?? 0;
        }
        container.__searchableFields = ["name", "username", "user_id", "url", "title", "metadata"];
        setListData(container, items, (item, parent) => {
            const row = createUserRow(item, {
                meta: () => buildActiveMeta(item),
                extra: () => buildProgressDisplay(item),
                onRowClick: () => showUserDetailsModal(item),
            });
            parent.appendChild(row);
        });
    }

    async function loadSuspiciousUsers(period = "today") {
        const data = await fetchJSON(endpoints.suspiciousUsers(period));
        const container = document.getElementById("suspicious-users-list");
        const items = data || [];
        container.__searchableFields = ["name", "username", "user_id"];
        setListData(container, items, (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    meta: () =>
                        `${formatUserMeta(item)} • ${replacePlaceholders(t("labels.downloads"), {
                            value: item.downloads ?? 0,
                        })}`,
                    extra: () => formatGapLabel(item.max_gap_seconds),
                    onRowClick: () => showUserDetailsModal(item),
                })
            );
        });
    }

    async function loadTopUsers(period) {
        const data = await fetchJSON(endpoints.topDownloaders(period));
        const container = document.getElementById("top-users-list");
        setListData(container, data || [], (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    extra: () => `${item.count ?? 0}`,
                })
            );
        });
    }

    async function loadCountries(period) {
        const data = await fetchJSON(endpoints.countries(period));
        const container = document.getElementById("countries-list");
        renderSimpleList(
            container,
            data || [],
            (item) => `${item.flag || "🏳"} ${item.country_code || "UN"}`,
            ""
        );
    }

    async function loadGenderAge(period) {
        const [gender, age] = await Promise.all([
            fetchJSON(endpoints.gender(period)),
            fetchJSON(endpoints.age(period)),
        ]);
        renderSimpleList(
            document.getElementById("gender-stats"),
            gender || [],
            (item) => `${item.gender}: ${item.count}`,
            ""
        );
        const ageContainer = document.getElementById("age-stats");
        if (ageContainer) {
            ageContainer.style.maxHeight = "400px";
            ageContainer.style.overflowY = "auto";
        }
        renderSimpleList(
            ageContainer,
            age || [],
            (item) => `${item.age_group}: ${item.count}`,
            "",
            false  // Don't show count badge (already in formatter)
        );
    }

    async function loadDomains(period) {
        const data = await fetchJSON(endpoints.domains(period));
        const container = document.getElementById("domains-list");
        renderSimpleList(container, data || [], (item) => item.domain || "-", "");
    }

    async function loadNSFW() {
        const [users, domains] = await Promise.all([
            fetchJSON(endpoints.nsfwUsers()),
            fetchJSON(endpoints.nsfwDomains()),
        ]);
        const usersContainer = document.getElementById("nsfw-users-list");
        setListData(usersContainer, users || [], (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    extra: () => `${item.count ?? 0}`,
                })
            );
        });
        const domainContainer = document.getElementById("nsfw-domains-list");
        renderSimpleList(domainContainer, domains || [], (item) => item.domain, "");
    }

    async function loadPlaylistUsers() {
        const data = await fetchJSON(endpoints.playlistUsers());
        const container = document.getElementById("playlist-users-list");
        setListData(container, data || [], (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    extra: () => `${item.count ?? 0}`,
                })
            );
        });
    }

    async function loadPowerUsers() {
        const minUrls = parseInt(document.getElementById("power-users-min-urls")?.value || "10", 10);
        const days = parseInt(document.getElementById("power-users-days")?.value || "7", 10);
        const data = await fetchJSON(endpoints.powerUsers(minUrls, days));
        const container = document.getElementById("power-users-list");
        setListData(container, data || [], (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    extra: () => replacePlaceholders(t("meta.days"), { value: item.streak ?? 0 }),
                })
            );
        });
    }

    function setupPowerUsersFilters() {
        const minUrlsInput = document.getElementById("power-users-min-urls");
        const daysInput = document.getElementById("power-users-days");
        const applyBtn = document.querySelector('[onclick="loadPowerUsers()"]');
        
        if (minUrlsInput && daysInput) {
            // Auto-reload on input change with debounce
            let timeout;
            const reload = () => {
                clearTimeout(timeout);
                timeout = setTimeout(() => {
                    loadPowerUsers();
                }, 500);
            };
            
            minUrlsInput.addEventListener("input", reload);
            daysInput.addEventListener("input", reload);
            
            // Also reload on Enter key
            minUrlsInput.addEventListener("keypress", (e) => {
                if (e.key === "Enter") {
                    clearTimeout(timeout);
                    loadPowerUsers();
                }
            });
            daysInput.addEventListener("keypress", (e) => {
                if (e.key === "Enter") {
                    clearTimeout(timeout);
                    loadPowerUsers();
                }
            });
        }
    }

    async function loadBlockedUsers() {
        const data = await fetchJSON(endpoints.blockedUsers());
        const container = document.getElementById("blocked-users-list");
        setListData(container, data || [], (item, parent) => {
            parent.appendChild(
                createUserRow(item, {
                    extra: () => new Date((item.timestamp || 0) * 1000).toLocaleDateString(),
                    unblock: true,
                })
            );
        });
    }

    async function loadChannelEvents() {
        const hours = document.body.dataset.channelHours || 48;
        const data = await fetchJSON(endpoints.channelEvents(hours));
        const container = document.getElementById("channel-events-list");
        if (!data || !data.length) {
            container.innerHTML = `<div class="empty-state">${emptyStateText}</div>`;
            return;
        }
        container.innerHTML = "";
        data.forEach((entry) => {
            const row = document.createElement("div");
            row.className = "timeline-entry";
            const icon = entry.type === "join" ? "🟢" : "🔴";
            const userName = entry.name || entry.username || `${t("meta.id_label")} ${entry.user_id}`;
            row.innerHTML = `
                <span class="marker">${icon}</span>
                <div class="body" style="flex: 1;">
                    <div class="title">${userName}</div>
                    <div class="time">${new Date(entry.timestamp * 1000).toLocaleString()}</div>
                    <div class="meta">${entry.description || ""}</div>
                </div>
                <div style="margin-left: auto;">
                    <button class="icon-button" data-block-user="${entry.user_id}" style="margin-left: 0.5rem;">❌</button>
                </div>
            `;
            const blockBtn = row.querySelector(`[data-block-user="${entry.user_id}"]`);
            if (blockBtn) {
                blockBtn.addEventListener("click", () => blockUser(entry.user_id));
            }
            container.appendChild(row);
        });
    }

    function setupTabs() {
        document.querySelectorAll(".tab-button").forEach((button) => {
            button.addEventListener("click", () => {
                document.querySelectorAll(".tab-button").forEach((btn) => btn.classList.remove("active"));
                document.querySelectorAll(".tab-panel").forEach((panel) => panel.classList.remove("active"));
                button.classList.add("active");
                const target = button.dataset.tabTarget;
                const panel = document.querySelector(`[data-tab-panel="${target}"]`);
                if (panel) panel.classList.add("active");
            });
        });
    }

    function setupExpandButtons() {
        document.querySelectorAll("[data-expand-button]").forEach((button) => {
            button.addEventListener("click", () => {
                const targetId = button.dataset.expandButton;
                const target = document.getElementById(targetId);
                if (target) {
                    target.dataset.expanded = target.dataset.expanded === "true" ? "false" : "true";
                    updateListView(target);
                }
            });
        });
    }

    function cacheSelectors() {
        selectors.topUsers = document.getElementById("top-users-period");
        selectors.countries = document.getElementById("countries-period");
        selectors.domains = document.getElementById("domains-period");
        selectors.suspicious = document.getElementById("suspicious-period");
        selectors.activePeriod = document.getElementById("active-users-period");
        selectors.activeCount = document.querySelector("[data-active-count]");
        themeToggleBtn = document.getElementById("theme-toggle");
    }

    function setupSelectors() {
        selectors.topUsers?.addEventListener("change", (event) => loadTopUsers(event.target.value));
        selectors.countries?.addEventListener("change", (event) => {
            const period = event.target.value;
            loadCountries(period);
            loadGenderAge(period);
        });
        selectors.domains?.addEventListener("change", (event) => loadDomains(event.target.value));
        selectors.suspicious?.addEventListener("change", (event) => loadSuspiciousUsers(event.target.value));
        if (selectors.activePeriod) {
            selectors.activePeriod.addEventListener("change", () => {
                loadActiveUsers();
                const minutes = selectors.activePeriod.value || "15";
                const subtitle = document.querySelector("[data-i18n='cards.active.subtitle']");
                if (subtitle) {
                    subtitle.dataset.minutes = minutes;
                    subtitle.textContent = replacePlaceholders(t("cards.active.subtitle"), { minutes });
                }
            });
        }
    }

    function setupLanguageSwitch() {
        document.querySelectorAll("[data-lang-btn]").forEach((button) => {
            button.addEventListener("click", () => setLanguage(button.dataset.langBtn));
        });
    }

    function applyTranslations() {
        document.documentElement.lang = currentLang;
        const dir = currentLang === "ar" ? "rtl" : "ltr";
        document.documentElement.dir = dir;
        document.body.dir = dir;
        const minutes = document.body.dataset.activeMinutes || "15";
        const hours = document.body.dataset.channelHours || "48";
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.dataset.i18n;
            let text = t(key);
            if (!text) return;
            text = replacePlaceholders(text, { minutes, hours });
            // Проверяем, является ли элемент кнопкой или input - для них используем textContent
            if (el.tagName === "BUTTON" || el.tagName === "INPUT" || el.tagName === "LABEL") {
                if (el.tagName === "INPUT" && el.type === "button") {
                    el.value = text;
                } else {
                    el.textContent = text;
                }
            } else {
                el.textContent = text;
            }
        });
        emptyStateText = t("misc.empty");
        document.querySelectorAll("[data-lang-btn]").forEach((button) => {
            button.classList.toggle("active", button.dataset.langBtn === currentLang);
        });
        document.querySelectorAll("[data-expand-button]").forEach((button) => {
            const target = document.getElementById(button.dataset.expandButton);
            if (target && target.__items && target.__items.length) {
                const expanded = target.dataset.expanded === "true";
                button.textContent = expanded ? t("buttons.collapse") : t("buttons.show_all");
            } else {
                button.textContent = t("buttons.show_all");
            }
        });
        updateThemeToggleLabel();
        updateStatusText();
    }

    function setLanguage(lang) {
        if (!translations[lang] || lang === currentLang) {
            return;
        }
        currentLang = lang;
        localStorage.setItem("dashboardLang", lang);
        applyTranslations();
        refreshData();
    }

    function setupSearchFilters() {
        const searchInputs = document.querySelectorAll(".search-input");
        searchInputs.forEach((input) => {
            const targetId = input.dataset.searchTarget || input.closest(".card")?.querySelector(".list")?.id;
            if (!targetId) return;
            input.addEventListener("input", (e) => {
                const query = e.target.value.toLowerCase().trim();
                const container = document.getElementById(targetId);
                if (!container || !container.__items) return;
                
                // Проверяем, это простой список или список с пользователями
                const isSimpleList = container.classList.contains("compact");
                
                if (isSimpleList) {
                    // Для простых списков фильтруем напрямую
                    const rows = container.querySelectorAll(".list-row");
                    rows.forEach((row) => {
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(query) ? "" : "none";
                    });
                } else {
                    // Для списков с пользователями используем updateListView
                    const filtered = container.__items.filter((item) => {
                        const searchable = [
                            item.name || "",
                            item.username || "",
                            String(item.user_id || ""),
                            item.url || "",
                            item.title || "",
                            item.domain || "",
                            item.country_code || "",
                        ].join(" ").toLowerCase();
                        return searchable.includes(query);
                    });
                    const originalItems = container.__items;
                    const originalExpanded = container.dataset.expanded;
                    container.__items = filtered;
                    container.dataset.expanded = "true";
                    updateListView(container);
                    container.__items = originalItems;
                    if (originalExpanded !== "true") {
                        container.dataset.expanded = originalExpanded;
                    }
                }
            });
        });
    }

    async function loadSystemMetrics() {
        const data = await fetchJSON("/api/system-metrics");
        const container = document.getElementById("system-metrics");
        if (data.error) {
            container.innerHTML = `<div class="empty-state">Error: ${data.error}</div>`;
            return;
        }
        const uptime = data.uptime || {};
        const reloadSeconds = data.next_reload?.seconds || 0;
        const reloadHours = Math.floor(reloadSeconds / 3600);
        const reloadMinutes = Math.floor((reloadSeconds % 3600) / 60);
        container.innerHTML = `
            <div class="metric-row">
                <span class="metric-label">Status:</span>
                <span class="metric-value">${data.status || "unknown"}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Uptime:</span>
                <span class="metric-value">${uptime.days || 0}d ${uptime.hours || 0}h ${uptime.minutes || 0}m</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Next cache reload:</span>
                <span class="metric-value">${reloadHours}h ${reloadMinutes}m</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">CPU:</span>
                <span class="metric-value">${data.cpu_percent || 0}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">RAM:</span>
                <span class="metric-value">${data.memory?.used_gb || 0} / ${data.memory?.total_gb || 0} GB (${data.memory?.percent || 0}%)</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Disk:</span>
                <span class="metric-value">${data.disk?.used_gb || 0} / ${data.disk?.total_gb || 0} GB (${data.disk?.percent || 0}%)</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Network sent:</span>
                <span class="metric-value">${data.network?.bytes_sent_mb || 0} MB</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Network received:</span>
                <span class="metric-value">${data.network?.bytes_recv_mb || 0} MB</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Network speed (sent):</span>
                <span class="metric-value">${data.network?.speed_sent_mbps || 0} Mbps</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Network speed (recv):</span>
                <span class="metric-value">${data.network?.speed_recv_mbps || 0} Mbps</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">External IP (IPv4):</span>
                <span class="metric-value">${data.external_ip?.ipv4 || data.external_ip || "unknown"}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">External IP (IPv6):</span>
                <span class="metric-value">${data.external_ip?.ipv6 || "unknown"}</span>
            </div>
            <div style="margin-top: 1rem; display: flex; gap: 0.5rem; flex-wrap: wrap;">
                <button class="action-button" onclick="rotateIP()" data-i18n="system.ip_rotate">Rotate IP</button>
                <button class="action-button" onclick="restartService()" data-i18n="system.restart">Restart Service</button>
                <button class="action-button" onclick="cleanupUserFiles()" data-i18n="system.cleanup">Cleanup User Files</button>
            </div>
        `;
    }

    async function loadPackageVersions() {
        const data = await fetchJSON("/api/package-versions");
        const container = document.getElementById("package-versions");
        container.innerHTML = Object.entries(data || {}).map(([pkg, version]) => `
            <div class="metric-row">
                <span class="metric-label">${pkg}:</span>
                <span class="metric-value">${version}</span>
            </div>
        `).join("") + `
            <div style="margin-top: 1rem;">
                <button class="action-button" onclick="updateEngines()" data-i18n="system.update_engines">Update Engines</button>
            </div>
        `;
    }

    window.rotateIP = async function() {
        if (!confirm("Rotate IP address? This will restart WireGuard.")) return;
        try {
            const data = await fetchJSON("/api/rotate-ip", { method: "POST" });
            let message = data.message || (data.status === "ok" ? "IP rotated successfully" : "Failed to rotate IP");
            if (data.status === "ok" && data.ipv4 && data.ipv6) {
                message += `\n\nNew IPv4: ${data.ipv4}\nNew IPv6: ${data.ipv6}`;
            }
            alert(message);
            if (data.status === "ok") {
                await loadSystemMetrics();
            }
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.restartService = async function() {
        if (!confirm("Restart tg-ytdlp-bot service?")) return;
        try {
            const data = await fetchJSON("/api/restart-service", { method: "POST" });
            alert(data.message || (data.status === "ok" ? "Service restarted successfully" : "Failed to restart service"));
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.updateEngines = async function() {
        if (!confirm("Update engines? This may take several minutes.")) return;
        try {
            const data = await fetchJSON("/api/update-engines", { method: "POST" });
            alert(data.message || (data.status === "ok" ? "Engines updated successfully" : "Failed to update engines"));
            if (data.status === "ok") {
                await loadPackageVersions();
            }
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.cleanupUserFiles = async function() {
        if (!confirm("Delete all user files (except system files)? This cannot be undone.")) return;
        try {
            const data = await fetchJSON("/api/cleanup-user-files", { method: "POST" });
            alert(data.message || (data.status === "ok" ? "Files cleaned up successfully" : "Failed to cleanup files"));
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.logout = async function() {
        try {
            await fetchJSON("/api/logout", { method: "POST" });
        } catch (e) {
            // даже если произошла ошибка, переходим на страницу логина
        } finally {
            window.location.href = "/login";
        }
    };

    async function loadConfigSettings() {
        const data = await fetchJSON("/api/config-settings");
        const container = document.getElementById("config-settings");
        if (!data) {
            container.innerHTML = `<div class="empty-state">${t("misc.empty")}</div>`;
            return;
        }
        const template = document.getElementById("config-setting-template");
        if (!template) {
            container.innerHTML = `<div class="empty-state">Layout template missing</div>`;
            return;
        }
        container.innerHTML = "";

        const rotationOptions = [
            { value: "random", label: "random" },
            { value: "round_robin", label: "round_robin" },
        ];

        const parseNumberList = (raw) =>
            raw
                .split(",")
                .map((v) => Number(v.trim()))
                .filter((num) => !Number.isNaN(num));

        const buildRow = (field) => {
            const node = template.content.firstElementChild.cloneNode(true);
            const labelEl = node.querySelector("[data-label]");
            labelEl.textContent = field.label;
            let control = node.querySelector("[data-input]");
            if (field.type === "select") {
                const select = document.createElement("select");
                select.className = control.className;
                (field.options || []).forEach((option) => {
                    const opt = document.createElement("option");
                    opt.value = option.value;
                    opt.textContent = option.label;
                    if (option.value === field.value) {
                        opt.selected = true;
                    }
                    select.appendChild(opt);
                });
                control.replaceWith(select);
                control = select;
            } else if (field.type === "number") {
                control.type = "number";
                control.value = field.value ?? "";
            } else {
                control.type = field.type === "password" ? "password" : "text";
                if (field.placeholder) {
                    control.placeholder = field.placeholder;
                }
                control.value = field.type === "list" && Array.isArray(field.value)
                    ? field.value.join(", ")
                    : field.value ?? "";
            }
            const saveButton = node.querySelector("[data-save]");
            saveButton.addEventListener("click", async () => {
                let newValue = control.value;
                try {
                    if (field.transform) {
                        newValue = field.transform(newValue);
                    } else if (field.type === "number") {
                        newValue = Number(newValue);
                        if (Number.isNaN(newValue)) {
                            throw new Error("Value must be a number");
                        }
                    } else if (field.type === "list") {
                        newValue = newValue
                            .split(",")
                            .map((v) => v.trim())
                            .filter((v) => v);
                    } else if (field.type === "password") {
                        // Для пароля - если пусто, не обновляем
                        if (!newValue || !newValue.trim()) {
                            alert("Password cannot be empty. Please enter a new password.");
                            return;
                        }
                    }
                    saveButton.disabled = true;
                    await fetchJSON("/api/update-config", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ key: field.key, value: newValue }),
                    });
                    if (field.type === "password") {
                        // Очищаем поле пароля после успешного сохранения
                        control.value = "";
                        alert("Password updated successfully. Please log in again with the new password.");
                    } else if (field.key === "DASHBOARD_USERNAME") {
                        alert("Username updated successfully. Please log in again with the new username.");
                    } else {
                        // Показываем успешное сохранение для других полей
                        const originalText = saveButton.textContent;
                        saveButton.textContent = "Saved!";
                        setTimeout(() => {
                            saveButton.textContent = originalText;
                        }, 2000);
                    }
                } catch (err) {
                    alert(err.message || err);
                } finally {
                    saveButton.disabled = false;
                }
            });
            return node;
        };

        const appendSection = (title, fields) => {
            if (!fields || !fields.length) {
                return;
            }
            const section = document.createElement("div");
            section.className = "config-section";
            if (title) {
                const heading = document.createElement("h4");
                heading.textContent = title;
                section.appendChild(heading);
            }
            fields.forEach((field) => {
                section.appendChild(buildRow(field));
            });
            container.appendChild(section);
        };

        appendSection("Proxy 1", data.proxy ? [
            { label: "Type", key: "PROXY_TYPE", value: data.proxy.type || "" },
            { label: "IP", key: "PROXY_IP", value: data.proxy.ip || "" },
            { label: "Port", key: "PROXY_PORT", value: data.proxy.port || "", type: "number" },
            { label: "User", key: "PROXY_USER", value: data.proxy.user || "" },
            { label: "Password", key: "PROXY_PASSWORD", value: data.proxy.password || "", type: "password" },
        ] : []);

        appendSection("Proxy 2", data.proxy_2 ? [
            { label: "Type", key: "PROXY_2_TYPE", value: data.proxy_2.type || "" },
            { label: "IP", key: "PROXY_2_IP", value: data.proxy_2.ip || "" },
            { label: "Port", key: "PROXY_2_PORT", value: data.proxy_2.port || "", type: "number" },
            { label: "User", key: "PROXY_2_USER", value: data.proxy_2.user || "" },
            { label: "Password", key: "PROXY_2_PASSWORD", value: data.proxy_2.password || "", type: "password" },
        ] : []);

        appendSection("Proxy strategy", [
            {
                label: "Selection mode",
                key: "PROXY_SELECT",
                value: data.proxy_select || "random",
                type: "select",
                options: rotationOptions,
            },
        ]);

        if (data.cookies) {
            const cookieFields = Object.entries(data.cookies).map(([name, url]) => ({
                label: `${name.toUpperCase()} cookie URL`,
                key: `${name.toUpperCase()}_COOKIE_URL`,
                value: url || "",
            }));
            appendSection("Service cookies", cookieFields);
        }

        const youtube = data.youtube_cookies || {};
        const youtubeFields = [
            {
                label: "Rotation mode",
                key: "YOUTUBE_COOKIE_ORDER",
                value: youtube.order || "round_robin",
                type: "select",
                options: rotationOptions,
            },
            { label: "Test URL", key: "YOUTUBE_COOKIE_TEST_URL", value: youtube.test_url || "" },
            { label: "Fallback cookie URL", key: "COOKIE_URL", value: youtube.cookie_url || "" },
            { label: "POT base URL", key: "YOUTUBE_POT_BASE_URL", value: youtube.pot_base_url || "" },
        ];
        const cookieList = youtube.list || [];
        // Всегда показываем 11 полей (YOUTUBE_COOKIE_URL + YOUTUBE_COOKIE_URL_1 до YOUTUBE_COOKIE_URL_10)
        // Если в списке меньше элементов, остальные будут пустыми
        for (let i = 0; i < 11; i += 1) {
            const key = i === 0 ? "YOUTUBE_COOKIE_URL" : `YOUTUBE_COOKIE_URL_${i}`;
            const value = (cookieList[i] !== undefined && cookieList[i] !== null) ? String(cookieList[i]) : "";
            youtubeFields.push({
                label: `Cookie #${i + 1}`,
                key,
                value: value || "",
            });
        }
        appendSection("YouTube cookies", youtubeFields);

        appendSection("Allowed groups", [
            {
                label: "Group IDs",
                key: "ALLOWED_GROUP",
                value: data.allowed_groups || [],
                type: "list",
                transform: (val) => parseNumberList(val),
            },
        ]);

        appendSection("Admins", [
            {
                label: "Admin IDs",
                key: "ADMIN",
                value: data.admins || [],
                type: "list",
                transform: (val) => parseNumberList(val),
            },
        ]);

        appendSection("Mini app", [
            { label: "Mini app URL", key: "MINIAPP_URL", value: data.miniapp_url || "" },
        ]);

        appendSection("Subscription link", [
            { label: "Subscribe link", key: "SUBSCRIBE_CHANNEL_URL", value: data.subscribe_channel_url || "" },
        ]);

        const dashboard = data.dashboard || {};
        appendSection("Dashboard authentication", [
            { label: "Username", key: "DASHBOARD_USERNAME", value: dashboard.username || "" },
            { label: "Password", key: "DASHBOARD_PASSWORD", value: "", type: "password", placeholder: "Enter new password" },
        ]);

        const channels = data.channels || {};
        appendSection("Logging channels", [
            { label: "Logs channel ID", key: "LOGS_ID", value: channels.logs_id || "", type: "number" },
            { label: "Video log ID", key: "LOGS_VIDEO_ID", value: channels.logs_video_id || "", type: "number" },
            { label: "NSFW log ID", key: "LOGS_NSFW_ID", value: channels.logs_nsfw_id || "", type: "number" },
            { label: "Image log ID", key: "LOGS_IMG_ID", value: channels.logs_img_id || "", type: "number" },
            { label: "Paid log ID", key: "LOGS_PAID_ID", value: channels.logs_paid_id || "", type: "number" },
            { label: "Exception log ID", key: "LOG_EXCEPTION", value: channels.log_exception || "", type: "number" },
            { label: "Subscribe channel ID", key: "SUBSCRIBE_CHANNEL", value: channels.subscribe_channel || "", type: "number" },
        ]);
    }

    async function loadListsStats() {
        const data = await fetchJSON("/api/lists-stats");
        const container = document.getElementById("lists-stats");
        container.innerHTML = `
            <div class="metric-row">
                <span class="metric-label">porn_domains.txt:</span>
                <span class="metric-value">${data.porn_domains || 0} lines</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">porn_keywords.txt:</span>
                <span class="metric-value">${data.porn_keywords || 0} lines</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">supported_sites.txt:</span>
                <span class="metric-value">${data.supported_sites || 0} lines</span>
            </div>
            <div style="margin-top: 1rem;">
                <button class="action-button" onclick="updateLists()" data-i18n="lists.update">Update Lists</button>
            </div>
        `;
    }

    window.updateLists = async function() {
        if (!confirm("Update lists? This may take several minutes.")) return;
        try {
            const data = await fetchJSON("/api/update-lists", { method: "POST" });
            alert(data.message || (data.status === "ok" ? "Lists updated successfully" : "Failed to update lists"));
            if (data.status === "ok") {
                await loadListsStats();
            }
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    async function loadDomainLists() {
        const data = await fetchJSON("/api/domain-lists");
        const container = document.getElementById("domain-lists-container");
        if (!data) {
            container.innerHTML = `<div class="empty-state">No domain lists</div>`;
            return;
        }
        let html = "";
        Object.entries(data).forEach(([listName, items]) => {
            html += `<div class="domain-list-section">`;
            html += `<h4>${listName} (${items.length})</h4>`;
            html += `<input type="text" class="list-search" data-list="${listName}" placeholder="Search...">`;
            html += `<div class="domain-list-items" data-list="${listName}">`;
            items.forEach((item, idx) => {
                html += `<div class="domain-list-item" data-item="${idx}">
                    <span>${item}</span>
                    <button class="icon-button-small" onclick="removeDomainItem('${listName}', ${idx})">✕</button>
                </div>`;
            });
            html += `</div>`;
            html += `<div class="add-item-form">
                <input type="text" class="new-item-input" data-list="${listName}" placeholder="Add new item...">
                <button onclick="addDomainItem('${listName}')">Add</button>
            </div>`;
            html += `<button class="save-list-btn" onclick="saveDomainList('${listName}')">Save ${listName}</button>`;
            html += `</div>`;
        });
        container.innerHTML = html;
        setupListSearches();
    }

    function setupListSearches() {
        document.querySelectorAll(".list-search").forEach((input) => {
            input.addEventListener("input", (e) => {
                const query = e.target.value.toLowerCase();
                const listName = e.target.dataset.list;
                const itemsContainer = document.querySelector(`.domain-list-items[data-list="${listName}"]`);
                if (!itemsContainer) return;
                itemsContainer.querySelectorAll(".domain-list-item").forEach((item) => {
                    const text = item.textContent.toLowerCase();
                    item.style.display = text.includes(query) ? "" : "none";
                });
            });
        });
    }

    window.removeDomainItem = function(listName, idx) {
        const itemsContainer = document.querySelector(`.domain-list-items[data-list="${listName}"]`);
        const item = itemsContainer?.querySelector(`[data-item="${idx}"]`);
        if (item) item.remove();
    };

    window.addDomainItem = function(listName) {
        const input = document.querySelector(`.new-item-input[data-list="${listName}"]`);
        const itemsContainer = document.querySelector(`.domain-list-items[data-list="${listName}"]`);
        if (!input || !itemsContainer || !input.value.trim()) return;
        const newItem = document.createElement("div");
        newItem.className = "domain-list-item";
        newItem.dataset.item = itemsContainer.children.length;
        newItem.innerHTML = `
            <span>${input.value.trim()}</span>
            <button class="icon-button-small" onclick="removeDomainItem('${listName}', ${newItem.dataset.item})">✕</button>
        `;
        itemsContainer.appendChild(newItem);
        input.value = "";
    };

    window.saveDomainList = async function(listName) {
        const itemsContainer = document.querySelector(`.domain-list-items[data-list="${listName}"]`);
        if (!itemsContainer) return;
        const items = Array.from(itemsContainer.querySelectorAll("span")).map(span => span.textContent.trim()).filter(v => v);
        try {
            await fetch("/api/update-domain-list", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ list_name: listName, items }),
            });
            alert(`${listName} saved! Restart bot to apply changes.`);
        } catch (e) {
            console.error(`Failed to save ${listName}:`, e);
            alert(`Failed to save ${listName}`);
        }
    };

    function refreshModeration() {
        loadBlockedUsers();
    }

    async function refreshData() {
        const topPeriod = selectors.topUsers?.value || "all";
        const countriesPeriod = selectors.countries?.value || "all";
        const domainsPeriod = selectors.domains?.value || "all";
        const suspiciousPeriod = selectors.suspicious?.value || "today";
        await Promise.all([
            loadActiveUsers(),
            loadTopUsers(topPeriod),
            loadCountries(countriesPeriod),
            loadGenderAge(countriesPeriod),
            loadDomains(domainsPeriod),
            loadNSFW(),
            loadPlaylistUsers(),
            loadPowerUsers(),
            loadBlockedUsers(),
            loadChannelEvents(),
            loadSuspiciousUsers(suspiciousPeriod),
        ]);
    }

    function setupTabHandlers() {
        document.querySelectorAll(".tab-button").forEach((button) => {
            button.addEventListener("click", async () => {
                const target = button.dataset.tabTarget;
                if (target === "system") {
                    await Promise.all([loadSystemMetrics(), loadPackageVersions(), loadConfigSettings()]);
                    applyTranslations();
                } else if (target === "lists") {
                    await Promise.all([loadListsStats(), loadDomainLists()]);
                    applyTranslations();
                } else if (target === "history") {
                    await loadHistoryUsers();
                    const periodSelect = document.getElementById("history-period");
                    if (periodSelect) {
                        periodSelect.addEventListener("change", () => {
                            if (currentHistoryUserId) {
                                loadUserHistory(currentHistoryUserId);
                            }
                        });
                    }
                    applyTranslations();
                }
            });
        });
    }

    async function bootstrap() {
        cacheSelectors();
        modalRoot = document.getElementById("modal-root");
        modalTitleEl = document.getElementById("modal-title");
        modalBodyEl = document.getElementById("modal-body");
        document.querySelectorAll("[data-modal-close]").forEach((btn) =>
            btn.addEventListener("click", closeModal)
        );
        if (modalRoot) {
            modalRoot.addEventListener("click", (event) => {
                if (event.target === modalRoot) {
                    closeModal();
                }
            });
        }
        document.addEventListener("keydown", (event) => {
            if (event.key === "Escape") {
                closeModal();
            }
        });
        setupTabs();
        setupExpandButtons();
        setupSelectors();
        setupLanguageSwitch();
        setupSearchFilters();
        setupTabHandlers();
        setupThemeToggle();
        setupPowerUsersFilters();
        applyTranslations();
        await refreshData();
    }

    document.addEventListener("DOMContentLoaded", bootstrap);
})();

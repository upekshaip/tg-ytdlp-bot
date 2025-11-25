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
            "tabs.system": "System",
            "tabs.lists": "Lists",
            "status.online": "ONLINE",
            "status.updating": "UPDATING…",
            "cards.active.title": "Active users",
            "cards.active.subtitle": "Sessions during last {minutes} minutes.",
            "cards.top_downloaders.title": "Top downloaders",
            "cards.top_downloaders.subtitle": "Pick a period for the ranking.",
            "cards.channel.title": "Channel activity ({hours}h)",
            "cards.channel.subtitle": "Join and leave events in the log channel.",
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
            "demographics.subtitle": "User statistics by country, gender, and age.",
            "demographics.countries": "Top Countries",
            "demographics.gender": "Gender",
            "demographics.age": "Age",
            "buttons.logout": "Logout",
            "buttons.save": "Save",
            "buttons.add": "Add"
        },
        ru: {
            "header.title": "Статистика бота",
            "header.subtitle": "Онлайн-дашборд для мониторинга активности Telegram-бота.",
            "tabs.activity": "Активность",
            "tabs.users": "Пользователи",
            "tabs.content": "Контент",
            "tabs.moderation": "Модерация",
            "tabs.system": "Система",
            "tabs.lists": "Списки",
            "status.online": "ОНЛАЙН",
            "status.updating": "ОБНОВЛЕНИЕ…",
            "cards.active.title": "Активные пользователи",
            "cards.active.subtitle": "Сессии за последние {minutes} минут.",
            "cards.top_downloaders.title": "Топ загрузчиков",
            "cards.top_downloaders.subtitle": "Выберите период для рейтинга.",
            "cards.channel.title": "Действия в канале ({hours}ч)",
            "cards.channel.subtitle": "Вступления и выходы в лог-канале.",
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
            "demographics.subtitle": "Статистика пользователей по странам, полу и возрасту.",
            "demographics.countries": "Топ стран",
            "demographics.gender": "Пол",
            "demographics.age": "Возраст",
            "buttons.logout": "Выход",
            "buttons.save": "Сохранить",
            "buttons.add": "Добавить"
        }
    };

    const selectors = {};
    let currentLang = "en";
    let statusMode = "online";
    let emptyStateText = translations.en["misc.empty"];

    const endpoints = {
        activeUsers: (limit = 100) => `/api/active-users?limit=${limit}`,
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

    async function fetchJSON(url) {
        setStatus("loading");
        try {
            const response = await fetch(url);
            if (!response.ok) {
                throw new Error(await response.text());
            }
            return await response.json();
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
        extraEl.textContent = options.extra ? options.extra(item) : "";
        if (options.hideButton) {
            button.remove();
        } else {
            button.textContent = options.unblock ? "✅" : "❌";
            button.addEventListener("click", () => {
                if (options.unblock) {
                    unblockUser(item.user_id);
                } else {
                    blockUser(item.user_id);
                }
            });
        }
        return node;
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

    function renderSimpleList(container, items, formatter, icon) {
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
            row.innerHTML = `
                <div class="list-row__info">
                    <span class="flag">${icon || "•"}</span>
                    <div>
                        <span class="title">${formatter(item)}</span>
                    </div>
                </div>
                <div class="badge">${item.count ?? ""}</div>
            `;
            container.appendChild(row);
        });
    }

    async function loadActiveUsers() {
        const data = await fetchJSON(endpoints.activeUsers());
        const container = document.getElementById("active-users-list");
        setListData(container, data.items || [], (item, parent) => {
            // Извлекаем домен из URL для более компактного отображения
            let urlDisplay = item.url || "";
            if (urlDisplay) {
                try {
                    const urlObj = new URL(urlDisplay);
                    urlDisplay = urlObj.hostname.replace("www.", "");
                } catch (e) {
                    // Если не удалось распарсить, оставляем как есть
                }
            }
            
            const row = createUserRow(item, {
                meta: () => {
                    let meta = `${formatUserMeta(item)}`;
                    if (urlDisplay) {
                        meta += ` • ${urlDisplay}`;
                    }
                    if (item.title) {
                        const titleShort = item.title.length > 50 ? item.title.substring(0, 50) + "..." : item.title;
                        meta += ` • ${titleShort}`;
                    }
                    return meta;
                },
                extra: () => {
                    if (item.progress !== undefined && item.progress !== null) {
                        const progressPercent = Math.round(item.progress);
                        return `<div style="display: flex; align-items: center; gap: 0.5rem;">
                            <div style="width: 120px; height: 10px; background: rgba(148, 163, 184, 0.2); border-radius: 5px; overflow: hidden;">
                                <div style="width: ${progressPercent}%; height: 100%; background: linear-gradient(120deg, #22d3ee, #a855f7); transition: width 0.3s;"></div>
                            </div>
                            <span style="font-size: 0.85rem; color: #38bdf8; font-weight: 600; min-width: 45px;">${progressPercent}%</span>
                        </div>`;
                    }
                    return relativeTime(item.last_event_ts);
                },
            });
            parent.appendChild(row);
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
        renderSimpleList(
            document.getElementById("age-stats"),
            age || [],
            (item) => `${item.age_group}: ${item.count}`,
            ""
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
    }

    function setupSelectors() {
        selectors.topUsers.addEventListener("change", (event) => loadTopUsers(event.target.value));
        selectors.countries.addEventListener("change", (event) => {
            loadCountries(event.target.value);
            loadGenderAge(event.target.value);
        });
        selectors.domains.addEventListener("change", (event) => loadDomains(event.target.value));
    }

    function setupLanguageSwitch() {
        document.querySelectorAll("[data-lang-btn]").forEach((button) => {
            button.addEventListener("click", () => setLanguage(button.dataset.langBtn));
        });
    }

    function applyTranslations() {
        document.documentElement.lang = currentLang;
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
        updateStatusText();
    }

    function setLanguage(lang) {
        if (!translations[lang] || lang === currentLang) {
            return;
        }
        currentLang = lang;
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
                <span class="metric-label">External IP:</span>
                <span class="metric-value">${data.external_ip || "unknown"}</span>
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
            const response = await fetch("/api/rotate-ip", { method: "POST" });
            const data = await response.json();
            alert(data.message || (data.status === "ok" ? "IP rotated successfully" : "Failed to rotate IP"));
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
            const response = await fetch("/api/restart-service", { method: "POST" });
            const data = await response.json();
            alert(data.message || (data.status === "ok" ? "Service restarted successfully" : "Failed to restart service"));
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.updateEngines = async function() {
        if (!confirm("Update engines? This may take several minutes.")) return;
        try {
            const response = await fetch("/api/update-engines", { method: "POST" });
            const data = await response.json();
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
            const response = await fetch("/api/cleanup-user-files", { method: "POST" });
            const data = await response.json();
            alert(data.message || (data.status === "ok" ? "Files cleaned up successfully" : "Failed to cleanup files"));
        } catch (e) {
            alert("Error: " + e.message);
        }
    };

    window.logout = async function() {
        try {
            await fetch("/api/logout", { method: "POST" });
            window.location.href = "/login";
        } catch (e) {
            window.location.href = "/login";
        }
    };

    async function loadConfigSettings() {
        const data = await fetchJSON("/api/config-settings");
        const container = document.getElementById("config-settings");
        if (!data) {
            container.innerHTML = `<div class="empty-state">No config data</div>`;
            return;
        }
        let html = "";
        if (data.proxy) {
            html += `<div class="config-section"><h4>Proxy 1</h4>`;
            html += `<div class="config-field"><label>Type:</label><input type="text" value="${data.proxy.type || ""}" data-config-key="PROXY_TYPE"></div>`;
            html += `<div class="config-field"><label>IP:</label><input type="text" value="${data.proxy.ip || ""}" data-config-key="PROXY_IP"></div>`;
            html += `<div class="config-field"><label>Port:</label><input type="text" value="${data.proxy.port || ""}" data-config-key="PROXY_PORT"></div>`;
            html += `<div class="config-field"><label>User:</label><input type="text" value="${data.proxy.user || ""}" data-config-key="PROXY_USER"></div>`;
            html += `<div class="config-field"><label>Password:</label><input type="password" value="${data.proxy.password || ""}" data-config-key="PROXY_PASSWORD"></div>`;
            html += `</div>`;
        }
        if (data.proxy_2) {
            html += `<div class="config-section"><h4>Proxy 2</h4>`;
            html += `<div class="config-field"><label>Type:</label><input type="text" value="${data.proxy_2.type || ""}" data-config-key="PROXY_2_TYPE"></div>`;
            html += `<div class="config-field"><label>IP:</label><input type="text" value="${data.proxy_2.ip || ""}" data-config-key="PROXY_2_IP"></div>`;
            html += `<div class="config-field"><label>Port:</label><input type="text" value="${data.proxy_2.port || ""}" data-config-key="PROXY_2_PORT"></div>`;
            html += `<div class="config-field"><label>User:</label><input type="text" value="${data.proxy_2.user || ""}" data-config-key="PROXY_2_USER"></div>`;
            html += `<div class="config-field"><label>Password:</label><input type="password" value="${data.proxy_2.password || ""}" data-config-key="PROXY_2_PASSWORD"></div>`;
            html += `</div>`;
        }
        if (data.cookies) {
            html += `<div class="config-section"><h4>Cookies</h4>`;
            Object.entries(data.cookies).forEach(([key, url]) => {
                const configKey = key.toUpperCase() + "_COOKIE_URL";
                html += `<div class="config-field"><label>${key}:</label><input type="text" value="${url || ""}" data-config-key="${configKey}"></div>`;
            });
            html += `</div>`;
        }
        if (data.allowed_groups) {
            html += `<div class="config-section"><h4>Allowed Groups</h4>`;
            html += `<div class="config-field"><label>Groups:</label><input type="text" value="${data.allowed_groups.join(", ")}" data-config-key="ALLOWED_GROUP"></div>`;
            html += `</div>`;
        }
        if (data.admins) {
            html += `<div class="config-section"><h4>Admins</h4>`;
            html += `<div class="config-field"><label>Admin IDs:</label><input type="text" value="${data.admins.join(", ")}" data-config-key="ADMIN"></div>`;
            html += `</div>`;
        }
        if (data.miniapp_url) {
            html += `<div class="config-section"><h4>MiniApp</h4>`;
            html += `<div class="config-field"><label>URL:</label><input type="text" value="${data.miniapp_url || ""}" data-config-key="MINIAPP_URL"></div>`;
            html += `</div>`;
        }
        if (data.subscribe_channel_url) {
            html += `<div class="config-section"><h4>Subscribe Channel</h4>`;
            html += `<div class="config-field"><label>URL:</label><input type="text" value="${data.subscribe_channel_url || ""}" data-config-key="SUBSCRIBE_CHANNEL_URL"></div>`;
            html += `</div>`;
        }
        html += `<button class="save-config-btn" onclick="saveConfigSettings()">Save Config</button>`;
        container.innerHTML = html;
    }

    window.saveConfigSettings = async function() {
        const inputs = document.querySelectorAll("#config-settings input[data-config-key]");
        for (const input of inputs) {
            const key = input.dataset.configKey;
            let value = input.value.trim();
            if (key === "ALLOWED_GROUP" || key === "ADMIN") {
                value = value.split(",").map(v => v.trim()).filter(v => v);
            }
            try {
                await fetch("/api/update-config", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ key, value }),
                });
            } catch (e) {
                console.error(`Failed to update ${key}:`, e);
            }
        }
        alert("Config updated! Restart bot to apply changes.");
    };

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
            const response = await fetch("/api/update-lists", { method: "POST" });
            const data = await response.json();
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
                }
            });
        });
    }

    async function bootstrap() {
        cacheSelectors();
        setupTabs();
        setupExpandButtons();
        setupSelectors();
        setupLanguageSwitch();
        setupSearchFilters();
        setupTabHandlers();
        applyTranslations();
        await refreshData();
    }

    document.addEventListener("DOMContentLoaded", bootstrap);
})();

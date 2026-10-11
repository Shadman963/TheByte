/**
 * The BYTE Cloud Kitchen - Kitchen Display System (KDS) & Staff Operations Module
 * Vanilla JavaScript (ES6+) for real-time status transitions, dynamic card updates,
 * non-destructive polling for new orders, sound notifications, and graceful form fallbacks.
 */

(function () {
    'use strict';

    let soundEnabled = true;
    let isPolling = false;
    let pollTimer = null;
    const POLL_INTERVAL_MS = 10000;
    const pendingUpdates = new Set();

    /**
     * CSRF helper.
     */
    function getCsrfToken() {
        if (window.ByteCart && typeof window.ByteCart.getCsrfToken === 'function') {
            return window.ByteCart.getCsrfToken();
        }
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput && tokenInput.value) return tokenInput.value;
        const cookies = document.cookie ? document.cookie.split(';') : [];
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith('csrftoken=')) {
                return decodeURIComponent(cookie.substring(10));
            }
        }
        return '';
    }

    /**
     * Toast notification helper.
     */
    function showNotification(msg, type = 'info') {
        if (window.ByteCart && typeof window.ByteCart.showToast === 'function') {
            window.ByteCart.showToast(msg, type);
            return;
        }
        alert(msg);
    }

    /**
     * Play synthesized kitchen order alert chime.
     */
    function playKitchenChime() {
        if (!soundEnabled) return;
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();
            if (ctx.state === 'suspended') ctx.resume();

            const osc = ctx.createOscillator();
            const gain = ctx.createGain();
            osc.type = 'sine';
            osc.frequency.setValueAtTime(880, ctx.currentTime); // A5 note
            osc.frequency.exponentialRampToValueAtTime(440, ctx.currentTime + 0.6);

            gain.gain.setValueAtTime(0.3, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.8);
        } catch (e) {
            // Audio context policy
        }
    }

    /**
     * Toggle staff sound notifications.
     */
    function toggleSoundAlert() {
        soundEnabled = !soundEnabled;
        const icon = document.getElementById('sound-icon');
        const text = document.getElementById('sound-text');
        if (icon && text) {
            if (soundEnabled) {
                icon.className = 'fa-solid fa-bell text-byte-amber';
                text.textContent = 'Sound: ON';
                playKitchenChime();
            } else {
                icon.className = 'fa-solid fa-bell-slash text-gray-400';
                text.textContent = 'Sound: OFF';
            }
        }
    }

    /**
     * Toggle Kitchen Open / Closed state via AJAX.
     */
    function toggleKitchenStatus() {
        const btn = document.getElementById('kitchen-status-toggle-btn');
        const textElem = document.getElementById('kitchen-status-toggle-text');
        if (btn) btn.disabled = true;

        fetch('/api/kitchen/toggle-open/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    showNotification(data.status_text, 'info');
                    if (btn && textElem) {
                        if (data.is_open) {
                            btn.className = 'px-4 py-2.5 rounded-xl font-bold text-xs transition flex items-center gap-2 shadow bg-emerald-100 text-emerald-800 border border-emerald-300 hover:bg-emerald-200';
                            textElem.textContent = 'Kitchen is OPEN';
                        } else {
                            btn.className = 'px-4 py-2.5 rounded-xl font-bold text-xs transition flex items-center gap-2 shadow bg-rose-100 text-rose-800 border border-rose-300 hover:bg-rose-200';
                            textElem.textContent = 'Kitchen is CLOSED';
                        }
                    }
                } else {
                    showNotification(data.message || 'Failed to toggle kitchen status', 'error');
                }
            })
            .catch(err => {
                console.error(err);
                showNotification('Network error toggling kitchen status.', 'error');
            })
            .finally(() => {
                if (btn) btn.disabled = false;
            });
    }

    /**
     * Update order status via AJAX with in-place card update and loading state.
     */
    function changeOrderStatus(orderId, newStatus, triggerBtn = null) {
        if (pendingUpdates.has(orderId)) return;
        pendingUpdates.add(orderId);

        let originalBtnHtml = '';
        if (triggerBtn) {
            triggerBtn.disabled = true;
            originalBtnHtml = triggerBtn.innerHTML;
            triggerBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin mr-1"></i> Updating...';
            triggerBtn.classList.add('opacity-75', 'cursor-not-allowed');
        }

        fetch(`/api/kitchen/order/${orderId}/update-status/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ status: newStatus })
        })
            .then(res => {
                return res.json().then(data => ({ ok: res.ok, status: res.status, body: data }));
            })
            .then(({ ok, status, body }) => {
                if (ok && body.success) {
                    showNotification(`Order #${body.order_number} marked as ${body.status_display}!`, 'success');
                    updateOrderCardInPlace(orderId, body);
                } else {
                    showNotification(body.message || `Failed to update order (${status})`, 'error');
                    if (triggerBtn) {
                        triggerBtn.disabled = false;
                        triggerBtn.innerHTML = originalBtnHtml;
                        triggerBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                    }
                }
            })
            .catch(err => {
                console.error('Order status update error:', err);
                showNotification('Network error while updating order status.', 'error');
                if (triggerBtn) {
                    triggerBtn.disabled = false;
                    triggerBtn.innerHTML = originalBtnHtml;
                    triggerBtn.classList.remove('opacity-75', 'cursor-not-allowed');
                }
            })
            .finally(() => {
                pendingUpdates.delete(orderId);
            });
    }

    /**
     * Update or transition an order card in the DOM without full page refresh.
     */
    function updateOrderCardInPlace(orderId, data) {
        const card = document.getElementById(`order-card-${orderId}`);
        if (!card) return;

        // If order reached a terminal state (delivered or cancelled), remove smoothly from active grid
        if (data.is_terminal || data.new_status === 'delivered' || data.new_status === 'cancelled') {
            card.classList.add('opacity-0', 'scale-95', 'transition-all', 'duration-500');
            setTimeout(() => {
                card.remove();
                updateActiveOrdersCount();
            }, 500);
            return;
        }

        // Update card border & status badge
        const badgeElem = card.querySelector('[data-order-status-badge]');
        const actionsContainer = card.querySelector('[data-order-actions]');

        // Border styling map
        card.classList.remove('border-amber-400', 'border-byte-maroon', 'border-purple-400', 'border-blue-400');
        if (data.new_status === 'pending') {
            card.classList.add('border-amber-400');
        } else if (data.new_status === 'preparing') {
            card.classList.add('border-byte-maroon');
        } else if (data.new_status === 'ready') {
            card.classList.add('border-purple-400');
        } else {
            card.classList.add('border-blue-400');
        }

        // Badge styling
        if (badgeElem) {
            badgeElem.textContent = data.status_display;
            badgeElem.className = 'px-3 py-1 rounded-full text-xs font-bold';
            if (data.new_status === 'pending') {
                badgeElem.classList.add('bg-amber-100', 'text-amber-800');
            } else if (data.new_status === 'preparing') {
                badgeElem.classList.add('bg-rose-100', 'text-rose-800', 'animate-pulse');
            } else if (data.new_status === 'ready') {
                badgeElem.classList.add('bg-purple-100', 'text-purple-800');
            } else {
                badgeElem.classList.add('bg-blue-100', 'text-blue-800');
            }
        }

        // Advance action buttons to the next logical step
        if (actionsContainer) {
            actionsContainer.innerHTML = '';
            const btnGroup = document.createElement('div');
            btnGroup.className = 'grid grid-cols-2 gap-2 text-xs font-bold';

            if (data.new_status === 'confirmed') {
                const cookBtn = document.createElement('button');
                cookBtn.type = 'button';
                cookBtn.className = 'col-span-2 py-2 rounded-xl bg-byte-maroon hover:bg-byte-maroonDark text-white transition';
                cookBtn.textContent = 'Start Cooking 🍳';
                cookBtn.addEventListener('click', () => changeOrderStatus(orderId, 'preparing', cookBtn));
                btnGroup.appendChild(cookBtn);
            } else if (data.new_status === 'preparing') {
                const packBtn = document.createElement('button');
                packBtn.type = 'button';
                packBtn.className = 'col-span-2 py-2 rounded-xl bg-purple-600 hover:bg-purple-700 text-white transition';
                packBtn.textContent = 'Mark Packed & Ready 📦';
                packBtn.addEventListener('click', () => changeOrderStatus(orderId, 'ready', packBtn));
                btnGroup.appendChild(packBtn);
            } else if (data.new_status === 'ready') {
                const riderBtn = document.createElement('button');
                riderBtn.type = 'button';
                riderBtn.className = 'col-span-2 py-2 rounded-xl bg-blue-600 hover:bg-blue-700 text-white transition';
                riderBtn.textContent = 'Hand to Rider 🛵';
                riderBtn.addEventListener('click', () => changeOrderStatus(orderId, 'out_for_delivery', riderBtn));
                btnGroup.appendChild(riderBtn);
            } else if (data.new_status === 'out_for_delivery') {
                const deliverBtn = document.createElement('button');
                deliverBtn.type = 'button';
                deliverBtn.className = 'col-span-2 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white transition';
                deliverBtn.textContent = 'Mark Delivered 🎉';
                deliverBtn.addEventListener('click', () => changeOrderStatus(orderId, 'delivered', deliverBtn));
                btnGroup.appendChild(deliverBtn);
            }

            actionsContainer.appendChild(btnGroup);

            // Cancel action link
            const footerRow = document.createElement('div');
            footerRow.className = 'flex justify-between items-center pt-2 text-[11px]';

            const trackLink = document.createElement('a');
            trackLink.href = `/order/track/${encodeURIComponent(data.order_number)}/`;
            trackLink.target = '_blank';
            trackLink.className = 'text-gray-500 hover:text-byte-maroon font-semibold';
            trackLink.innerHTML = '<i class="fa-solid fa-arrow-up-right-from-square mr-1"></i> Customer View';

            const cancelBtn = document.createElement('button');
            cancelBtn.type = 'button';
            cancelBtn.className = 'text-rose-600 hover:underline font-semibold';
            cancelBtn.textContent = 'Cancel Order';
            cancelBtn.addEventListener('click', () => {
                if (confirm(`Cancel order #${data.order_number}?`)) {
                    changeOrderStatus(orderId, 'cancelled', cancelBtn);
                }
            });

            footerRow.appendChild(trackLink);
            footerRow.appendChild(cancelBtn);
            actionsContainer.appendChild(footerRow);
        }

        updateActiveOrdersCount();
    }

    /**
     * Recount active orders on the screen.
     */
    function updateActiveOrdersCount() {
        const cards = document.querySelectorAll('[id^="order-card-"]');
        const countDisplay = document.getElementById('active-orders-count-badge');
        if (countDisplay) {
            countDisplay.textContent = cards.length;
        }
    }

    /**
     * Poll staff orders API to discover newly created orders.
     */
    function pollKitchenOrders() {
        if (isPolling) return;
        isPolling = true;

        fetch('/api/staff/orders/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(res => {
                if (!res.ok) throw new Error(`Staff orders error: ${res.status}`);
                return res.json();
            })
            .then(data => {
                if (data.success && Array.isArray(data.orders)) {
                    const currentCards = document.querySelectorAll('[id^="order-card-"]');
                    const existingIds = new Set();
                    currentCards.forEach(c => {
                        const id = c.id.replace('order-card-', '');
                        if (id) existingIds.add(parseInt(id, 10));
                    });

                    // Check for new incoming orders
                    let hasNew = false;
                    data.orders.forEach(o => {
                        if (!existingIds.has(o.id)) {
                            hasNew = true;
                        }
                    });

                    if (hasNew) {
                        playKitchenChime();
                        showNotification('🔔 New customer order received!', 'info');
                        // Show banner to refresh active queue seamlessly
                        const banner = document.getElementById('new-order-alert-banner');
                        if (banner) {
                            banner.classList.remove('hidden');
                        }
                    }

                    // Update KPI counters
                    const kpiActive = document.getElementById('kpi-cooking-count');
                    if (kpiActive && data.active_count !== undefined) {
                        kpiActive.textContent = `${data.active_count} Active`;
                    }
                    const kpiToday = document.getElementById('kpi-today-count');
                    if (kpiToday && data.today_count !== undefined) {
                        kpiToday.textContent = `${data.today_count} Orders`;
                    }
                }
            })
            .catch(err => {
                // Silently retry on next poll interval
                console.warn('Kitchen poll error:', err.message);
            })
            .finally(() => {
                isPolling = false;
            });
    }

    /**
     * Progressive enhancement for standard form fallback.
     */
    function attachFormEnhancements() {
        document.addEventListener('submit', function (e) {
            const form = e.target;
            if (form.matches('.kitchen-status-form')) {
                e.preventDefault();
                const orderId = form.dataset.orderId || form.querySelector('[name=order_id]')?.value;
                const status = form.querySelector('[name=status]')?.value;
                const btn = form.querySelector('button[type=submit]');
                if (orderId && status) {
                    changeOrderStatus(orderId, status, btn);
                }
            }
        });
    }

    /**
     * Initialize KDS / Staff portal.
     */
    function initKitchenDashboard() {
        attachFormEnhancements();

        // Start background polling
        if (!pollTimer) {
            pollTimer = setInterval(pollKitchenOrders, POLL_INTERVAL_MS);
        }

        // Pause polling when tab is hidden
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                if (pollTimer) {
                    clearInterval(pollTimer);
                    pollTimer = null;
                }
            } else {
                if (!pollTimer) {
                    pollKitchenOrders();
                    pollTimer = setInterval(pollKitchenOrders, POLL_INTERVAL_MS);
                }
            }
        });
    }

    // Expose helpers globally
    window.ByteKitchen = {
        changeOrderStatus,
        toggleKitchenStatus,
        toggleSoundAlert,
        pollKitchenOrders
    };

    window.changeOrderStatus = changeOrderStatus;
    window.toggleKitchenStatus = toggleKitchenStatus;
    window.toggleSoundAlert = toggleSoundAlert;

    document.addEventListener('DOMContentLoaded', initKitchenDashboard);

})();

/**
 * The BYTE Cloud Kitchen - Live Order Tracking Module
 * Lightweight Vanilla JavaScript with 8-second polling, overlapping request prevention,
 * terminal state shutdown, visibility state management, and accessible UI updates.
 */

(function () {
    'use strict';

    const STATUS_MAP = {
        'pending': { index: 0, label: 'Order Received', color: 'bg-byte-amber text-white' },
        'confirmed': { index: 1, label: 'Order Confirmed', color: 'bg-byte-maroon text-white' },
        'preparing': { index: 2, label: 'Kitchen Preparing 🍳', color: 'bg-byte-maroon text-white animate-pulse' },
        'ready': { index: 3, label: 'Ready for Delivery 🛵', color: 'bg-byte-amber text-white' },
        'out_for_delivery': { index: 4, label: 'Out for Delivery 🚀', color: 'bg-blue-600 text-white animate-pulse' },
        'delivered': { index: 5, label: 'Delivered 🎉', color: 'bg-emerald-600 text-white' },
        'cancelled': { index: -1, label: 'Cancelled ❌', color: 'bg-rose-600 text-white' }
    };

    const STEPPER_PERCENTAGES = ['10%', '28%', '48%', '68%', '85%', '100%'];
    const POLL_INTERVAL_MS = 8000;

    let pollTimer = null;
    let isPolling = false;
    let orderNumber = null;
    let currentStatus = null;
    let isTerminal = false;

    /**
     * Play gentle chime on status update using Web Audio API.
     */
    function playStatusChime() {
        try {
            const AudioCtx = window.AudioContext || window.webkitAudioContext;
            if (!AudioCtx) return;
            const ctx = new AudioCtx();
            if (ctx.state === 'suspended') {
                ctx.resume();
            }
            const osc = ctx.createOscillator();
            const gain = ctx.createGain();

            osc.type = 'triangle';
            osc.frequency.setValueAtTime(523.25, ctx.currentTime); // C5
            osc.frequency.setValueAtTime(659.25, ctx.currentTime + 0.15); // E5
            osc.frequency.setValueAtTime(783.99, ctx.currentTime + 0.3); // G5

            gain.gain.setValueAtTime(0.25, ctx.currentTime);
            gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.7);

            osc.connect(gain);
            gain.connect(ctx.destination);
            osc.start();
            osc.stop(ctx.currentTime + 0.7);
        } catch (e) {
            // Audio context restrictions may apply prior to user interaction
        }
    }

    /**
     * Update the visual order status, stepper, and progress bar without unnecessary re-renders.
     */
    function applyStatusUpdate(data) {
        if (!data || !data.order_status) return;

        const st = STATUS_MAP[data.order_status] || {
            index: -1,
            label: data.status_display || data.order_status,
            color: 'bg-gray-600 text-white'
        };

        const hasChanged = data.order_status !== currentStatus;
        currentStatus = data.order_status;

        // 1. Update status badge
        const badge = document.getElementById('live-status-badge');
        const text = document.getElementById('live-status-text');
        if (badge && text) {
            badge.className = `inline-flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-extrabold shadow-md ${st.color}`;
            text.textContent = st.label;
        }

        // 2. Update Stepper circles
        const steps = document.querySelectorAll('.step-item > div[data-step]');
        steps.forEach(s => {
            const stepIdx = parseInt(s.dataset.step, 10);
            if (st.index >= 0 && stepIdx <= st.index) {
                s.classList.remove('bg-gray-200', 'text-gray-500');
                if (stepIdx === 5) {
                    s.classList.remove('bg-byte-maroon');
                    s.classList.add('bg-emerald-600', 'text-white');
                } else {
                    s.classList.add('bg-byte-maroon', 'text-white');
                }
            } else {
                s.classList.add('bg-gray-200', 'text-gray-500');
                s.classList.remove('bg-byte-maroon', 'bg-emerald-600', 'text-white');
            }
        });

        // 3. Update Stepper connecting bar
        const bar = document.getElementById('stepper-progress-bar');
        if (bar) {
            bar.style.width = st.index >= 0 ? STEPPER_PERCENTAGES[st.index] : '0%';
        }

        // 4. Update live indicator
        const indicator = document.getElementById('auto-refresh-indicator');
        if (indicator) {
            if (data.is_terminal || data.order_status === 'delivered' || data.order_status === 'cancelled') {
                indicator.innerHTML = '<span class="text-white/80 font-semibold"><i class="fa-solid fa-flag-checkered mr-1"></i> Order finalized</span>';
            } else if (hasChanged) {
                indicator.innerHTML = '<span class="text-emerald-300 font-bold"><i class="fa-solid fa-check mr-1"></i> Just updated!</span>';
                setTimeout(() => {
                    if (!isTerminal && indicator) {
                        indicator.innerHTML = '<i class="fa-solid fa-rotate text-xs animate-spin mr-1"></i> Live updating every 8s';
                    }
                }, 3000);
            }
        }

        // 5. Audio chime & toast notification if state changed
        if (hasChanged) {
            playStatusChime();
            if (window.ByteCart && typeof window.ByteCart.showToast === 'function') {
                window.ByteCart.showToast(
                    `Order #${data.order_number}: ${st.label}`,
                    data.order_status === 'delivered' ? 'success' : 'info'
                );
            }
        }

        // 6. Check if terminal state reached
        if (data.is_terminal || data.order_status === 'delivered' || data.order_status === 'cancelled') {
            stopPolling();
        }
    }

    /**
     * Poll order status from the minimal, secure endpoint.
     */
    function pollOrderStatus() {
        if (!orderNumber || isTerminal || isPolling) return;
        isPolling = true;

        fetch(`/api/order/${encodeURIComponent(orderNumber)}/status/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(res => {
                if (res.status === 404 || res.status === 403) {
                    stopPolling();
                    return null;
                }
                if (!res.ok) {
                    throw new Error(`Tracking poll error: ${res.status}`);
                }
                return res.json();
            })
            .then(data => {
                if (data && data.found) {
                    applyStatusUpdate(data);
                }
            })
            .catch(err => {
                // Network error: don't crash, will retry on next poll interval
                console.warn('Live tracking update failed, will retry:', err.message);
            })
            .finally(() => {
                isPolling = false;
            });
    }

    /**
     * Start the 8-second polling timer.
     */
    function startPolling() {
        if (isTerminal || pollTimer) return;
        pollTimer = setInterval(pollOrderStatus, POLL_INTERVAL_MS);
    }

    /**
     * Stop polling immediately.
     */
    function stopPolling() {
        isTerminal = true;
        if (pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
        }
    }

    /**
     * Handle page visibility change (pause when tab hidden, resume when visible).
     */
    function handleVisibilityChange() {
        if (document.hidden) {
            if (pollTimer) {
                clearInterval(pollTimer);
                pollTimer = null;
            }
        } else {
            if (!isTerminal && !pollTimer) {
                pollOrderStatus();
                startPolling();
            }
        }
    }

    /**
     * Initialization.
     */
    function initOrderTracking() {
        const orderDisplay = document.getElementById('order-number-display');
        const container = document.getElementById('order-tracking-active');

        if (!orderDisplay && !container) return;

        orderNumber = (orderDisplay ? orderDisplay.textContent : container?.dataset.orderNumber || '').trim();
        if (!orderNumber) return;

        const liveBadge = document.getElementById('live-status-text');
        if (liveBadge) {
            currentStatus = container?.dataset.initialStatus || '';
        }

        // Check if initial status is already terminal
        if (currentStatus === 'delivered' || currentStatus === 'cancelled') {
            stopPolling();
            return;
        }

        // Bind visibility & unload events to conserve network & battery
        document.addEventListener('visibilitychange', handleVisibilityChange);
        window.addEventListener('beforeunload', stopPolling);
        window.addEventListener('pagehide', stopPolling);

        // Start 8-second timer
        startPolling();
    }

    // Expose for external control if needed
    window.ByteOrderTracker = {
        init: initOrderTracking,
        stop: stopPolling,
        pollNow: pollOrderStatus
    };

    document.addEventListener('DOMContentLoaded', initOrderTracking);

})();

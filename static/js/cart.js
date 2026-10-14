/**
 * The BYTE Cloud Kitchen - Shopping Cart & Global Interaction Module
 * Vanilla JavaScript (ES6+) with progressive enhancement, CSRF handling, and safe DOM manipulation.
 */

(function () {
    'use strict';

    // In-flight request guards to prevent race conditions & duplicate submissions
    const pendingRequests = new Set();

    /**
     * Retrieve CSRF token from DOM or cookie.
     */
    function getCsrfToken() {
        const tokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (tokenInput && tokenInput.value) {
            return tokenInput.value;
        }
        return getCookie('csrftoken') || '';
    }

    /**
     * Retrieve cookie value by name.
     */
    function getCookie(name) {
        if (!document.cookie) return null;
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.startsWith(name + '=')) {
                return decodeURIComponent(cookie.substring(name.length + 1));
            }
        }
        return null;
    }

    /**
     * Display accessible toast message with auto-dismiss.
     */
    function showToast(message, type = 'info') {
        const existingToasts = document.querySelectorAll('.byte-toast');
        existingToasts.forEach(t => t.remove());

        const toast = document.createElement('div');
        toast.className = 'byte-toast fixed bottom-20 left-3 right-3 sm:left-auto sm:bottom-24 sm:right-6 z-50 p-3.5 sm:p-4 rounded-2xl shadow-2xl text-white font-bold text-xs sm:text-sm flex items-center gap-3 transition-all duration-300 transform translate-y-10 opacity-0';
        toast.setAttribute('role', 'alert');
        toast.setAttribute('aria-live', 'polite');

        let bgClass = 'bg-byte-maroon';
        let iconClass = 'fa-solid fa-circle-info';
        if (type === 'success') {
            bgClass = 'bg-emerald-600';
            iconClass = 'fa-solid fa-circle-check';
        } else if (type === 'error') {
            bgClass = 'bg-rose-600';
            iconClass = 'fa-solid fa-triangle-exclamation';
        }

        toast.classList.add(bgClass);

        const icon = document.createElement('i');
        icon.className = iconClass + ' shrink-0';
        const textSpan = document.createElement('span');
        textSpan.className = 'min-w-0 flex-1 break-words whitespace-normal leading-snug';
        textSpan.textContent = message;

        toast.appendChild(icon);
        toast.appendChild(textSpan);
        document.body.appendChild(toast);

        requestAnimationFrame(() => {
            toast.classList.remove('translate-y-10', 'opacity-0');
        });

        setTimeout(() => {
            toast.classList.add('translate-y-10', 'opacity-0');
            setTimeout(() => toast.remove(), 350);
        }, 3200);
    }

    // Modal state
    let currentModalItem = null;
    let currentModalQty = 1;

    /**
     * Fetch item details and open customization modal.
     */
    function openItemModal(itemId) {
        if (pendingRequests.has(`item-${itemId}`)) return;
        pendingRequests.add(`item-${itemId}`);

        fetch(`/api/item/${itemId}/`, {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(res => {
                if (!res.ok) throw new Error(`HTTP error ${res.status}`);
                return res.json();
            })
            .then(item => {
                currentModalItem = item;
                currentModalQty = 1;

                const categoryElem = document.getElementById('modal-category');
                const titleElem = document.getElementById('modal-title');
                const taglineElem = document.getElementById('modal-tagline');
                const descElem = document.getElementById('modal-description');
                const portionElem = document.getElementById('modal-portion');
                const imgElem = document.getElementById('modal-image');
                const qtyElem = document.getElementById('modal-qty');
                const instructionsElem = document.getElementById('modal-instructions');

                if (categoryElem) categoryElem.textContent = item.category || '';
                if (titleElem) titleElem.textContent = item.name || '';
                if (taglineElem) taglineElem.textContent = item.tagline || '';
                if (descElem) descElem.textContent = item.description || '';
                if (portionElem) portionElem.textContent = item.portion_size || '';
                if (imgElem) imgElem.src = item.image || '/static/images/hero_banner.png';
                if (qtyElem) qtyElem.textContent = '1';
                if (instructionsElem) instructionsElem.value = '';

                // Addons list
                const addonsSection = document.getElementById('modal-addons-section');
                const addonsContainer = document.getElementById('modal-addons-list');
                if (addonsContainer) {
                    addonsContainer.innerHTML = '';
                    if (item.addons && item.addons.length > 0) {
                        if (addonsSection) addonsSection.classList.remove('hidden');
                        item.addons.forEach(a => {
                            const label = document.createElement('label');
                            label.className = 'flex items-start sm:items-center justify-between gap-2 p-2.5 rounded-lg border border-gray-200 hover:bg-byte-cream/40 cursor-pointer transition text-xs font-semibold';

                            const leftDiv = document.createElement('div');
                            leftDiv.className = 'flex items-start sm:items-center gap-2 min-w-0 flex-1';

                            const chk = document.createElement('input');
                            chk.type = 'checkbox';
                            chk.name = 'modal_addons';
                            chk.value = a.id;
                            chk.dataset.price = a.price;
                            chk.className = 'rounded text-byte-maroon focus:ring-byte-maroon w-4 h-4 mt-0.5 sm:mt-0 shrink-0';
                            chk.addEventListener('change', recalcModalTotal);

                            const nameSpan = document.createElement('span');
                            nameSpan.className = 'break-words whitespace-normal leading-snug';
                            nameSpan.textContent = a.name;

                            leftDiv.appendChild(chk);
                            leftDiv.appendChild(nameSpan);

                            const priceSpan = document.createElement('span');
                            priceSpan.className = 'text-byte-maroon font-bold shrink-0';
                            priceSpan.textContent = `+৳${parseFloat(a.price).toFixed(2)}`;

                            label.appendChild(leftDiv);
                            label.appendChild(priceSpan);
                            addonsContainer.appendChild(label);
                        });
                    } else if (addonsSection) {
                        addonsSection.classList.add('hidden');
                    }
                }

                recalcModalTotal();

                // Open modal display
                const modal = document.getElementById('item-modal');
                const backdrop = document.getElementById('item-modal-backdrop');
                if (modal && backdrop) {
                    modal.classList.remove('hidden');
                    void modal.offsetWidth;
                    backdrop.classList.remove('opacity-0', 'pointer-events-none');
                    const card = modal.querySelector('> div');
                    if (card) {
                        card.classList.remove('scale-95', 'opacity-0');
                        card.classList.add('scale-100', 'opacity-100');
                    }
                }
            })
            .catch(err => {
                console.error('Failed to load item:', err);
                showToast('Could not load item details. Please check connection.', 'error');
            })
            .finally(() => {
                pendingRequests.delete(`item-${itemId}`);
            });
    }

    /**
     * Close item customization modal.
     */
    function closeItemModal() {
        const modal = document.getElementById('item-modal');
        const backdrop = document.getElementById('item-modal-backdrop');
        if (!modal || !backdrop) return;

        backdrop.classList.add('opacity-0', 'pointer-events-none');
        const card = modal.querySelector('> div');
        if (card) {
            card.classList.add('scale-95', 'opacity-0');
            card.classList.remove('scale-100', 'opacity-100');
        }
        setTimeout(() => {
            modal.classList.add('hidden');
            currentModalItem = null;
        }, 220);
    }

    /**
     * Adjust quantity in customization modal.
     */
    function adjustModalQty(delta) {
        currentModalQty = Math.max(1, Math.min(50, currentModalQty + delta));
        const qtyElem = document.getElementById('modal-qty');
        if (qtyElem) qtyElem.textContent = currentModalQty;
        recalcModalTotal();
    }

    /**
     * Recalculate total price within item modal.
     */
    function recalcModalTotal() {
        if (!currentModalItem) return;
        let unitPrice = parseFloat(currentModalItem.final_price || currentModalItem.price || 0);
        const checkedAddons = document.querySelectorAll('input[name="modal_addons"]:checked');
        checkedAddons.forEach(chk => {
            unitPrice += parseFloat(chk.dataset.price || 0);
        });
        const total = unitPrice * currentModalQty;
        const totalElem = document.getElementById('modal-total-price');
        if (totalElem) totalElem.textContent = total.toFixed(2);
    }

    /**
     * Submit modal choices to cart.
     */
    function submitModalAddToCart() {
        if (!currentModalItem) return;
        const instructionsElem = document.getElementById('modal-instructions');
        const instructions = instructionsElem ? instructionsElem.value.trim() : '';
        const addonCheckboxes = document.querySelectorAll('input[name="modal_addons"]:checked');
        const addonIds = Array.from(addonCheckboxes).map(chk => parseInt(chk.value, 10));

        const submitBtn = document.getElementById('modal-add-btn');
        addToCart(currentModalItem.id, currentModalQty, instructions, addonIds, submitBtn);
        closeItemModal();
    }

    /**
     * Cart Drawer open/close/toggle.
     */
    function openCartDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const backdrop = document.getElementById('cart-drawer-backdrop');
        if (drawer && backdrop) {
            drawer.classList.remove('translate-x-full');
            backdrop.classList.remove('opacity-0', 'pointer-events-none');
            refreshCartDrawer();
        }
    }

    function closeCartDrawer() {
        const drawer = document.getElementById('cart-drawer');
        const backdrop = document.getElementById('cart-drawer-backdrop');
        if (drawer && backdrop) {
            drawer.classList.add('translate-x-full');
            backdrop.classList.add('opacity-0', 'pointer-events-none');
        }
    }

    function toggleCartDrawer() {
        const drawer = document.getElementById('cart-drawer');
        if (!drawer) return;
        if (drawer.classList.contains('translate-x-full')) {
            openCartDrawer();
        } else {
            closeCartDrawer();
        }
    }

    /**
     * Add an item to the shopping cart.
     */
    function addToCart(itemId, quantity = 1, instructions = '', addonIds = [], triggerBtn = null) {
        const reqKey = `add-${itemId}`;
        if (pendingRequests.has(reqKey)) return;
        pendingRequests.add(reqKey);

        let originalBtnHtml = '';
        if (triggerBtn) {
            triggerBtn.disabled = true;
            originalBtnHtml = triggerBtn.innerHTML;
            triggerBtn.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin text-xs"></i>';
        }

        fetch('/api/cart/add/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({
                item_id: itemId,
                quantity: quantity,
                special_instructions: instructions,
                addon_ids: addonIds
            })
        })
            .then(res => {
                return res.json().then(data => ({ status: res.status, body: data }));
            })
            .then(({ status, body }) => {
                if (status >= 200 && status < 300 && body.success) {
                    updateCartUI(body);
                    renderDrawerItems(body);
                    showToast(body.message || 'Added to cart!', 'success');

                    // Animate navigation badge
                    const badge = document.getElementById('nav-cart-badge');
                    if (badge) {
                        badge.classList.add('scale-125');
                        setTimeout(() => badge.classList.remove('scale-125'), 250);
                    }

                    // Animate floating cart button
                    const floatingBtn = document.getElementById('floating-cart-btn');
                    if (floatingBtn) {
                        floatingBtn.classList.add('scale-105', 'ring-4', 'ring-byte-amber/50');
                        setTimeout(() => floatingBtn.classList.remove('scale-105', 'ring-4', 'ring-byte-amber/50'), 300);
                    }
                } else {
                    showToast(body.message || 'Could not add item to cart.', 'error');
                }
            })
            .catch(err => {
                console.error('Add to cart error:', err);
                showToast('Network error while adding to cart. Please retry.', 'error');
            })
            .finally(() => {
                pendingRequests.delete(reqKey);
                if (triggerBtn) {
                    triggerBtn.disabled = false;
                    triggerBtn.innerHTML = originalBtnHtml;
                }
            });
    }

    /**
     * Change quantity of a cart item (+1 or -1).
     */
    function changeCartQty(key, delta, triggerBtn = null) {
        const reqKey = `qty-${key}`;
        if (pendingRequests.has(reqKey)) return;
        pendingRequests.add(reqKey);

        if (triggerBtn) {
            triggerBtn.disabled = true;
            triggerBtn.classList.add('opacity-50');
        }

        fetch('/api/cart/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ key: key, delta: delta })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    updateCartUI(data);
                    renderDrawerItems(data);
                    syncCartPageItem(key, data);
                } else {
                    showToast(data.message || 'Could not update quantity.', 'error');
                }
            })
            .catch(err => {
                console.error('Update cart error:', err);
                showToast('Failed to update item quantity.', 'error');
            })
            .finally(() => {
                pendingRequests.delete(reqKey);
                if (triggerBtn) {
                    triggerBtn.disabled = false;
                    triggerBtn.classList.remove('opacity-50');
                }
            });
    }

    /**
     * Set exact quantity for a cart item.
     */
    function updateCartQty(key, quantity, inputElem = null) {
        const reqKey = `qty-${key}`;
        if (pendingRequests.has(reqKey)) return;
        pendingRequests.add(reqKey);

        fetch('/api/cart/update/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ key: key, quantity: quantity })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    updateCartUI(data);
                    renderDrawerItems(data);
                    syncCartPageItem(key, data);
                } else {
                    showToast(data.message || 'Could not update cart.', 'error');
                }
            })
            .catch(err => {
                console.error(err);
                showToast('Error updating item quantity.', 'error');
            })
            .finally(() => {
                pendingRequests.delete(reqKey);
            });
    }

    /**
     * Remove an item from the cart entirely.
     */
    function removeCartItem(key, triggerBtn = null) {
        const reqKey = `remove-${key}`;
        if (pendingRequests.has(reqKey)) return;
        pendingRequests.add(reqKey);

        if (triggerBtn) {
            triggerBtn.disabled = true;
            triggerBtn.classList.add('opacity-50');
        }

        fetch('/api/cart/remove/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify({ key: key })
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    updateCartUI(data);
                    renderDrawerItems(data);
                    // Remove row from Cart page if present
                    const itemRow = document.querySelector(`[data-cart-item-key="${CSS.escape(key)}"]`);
                    if (itemRow) {
                        itemRow.classList.add('opacity-0', 'scale-95', 'transition-all', 'duration-300');
                        setTimeout(() => itemRow.remove(), 300);
                    }
                    showToast('Item removed from cart', 'info');
                } else {
                    showToast(data.message || 'Error removing item', 'error');
                }
            })
            .catch(err => {
                console.error('Remove cart error:', err);
                showToast('Failed to remove item.', 'error');
            })
            .finally(() => {
                pendingRequests.delete(reqKey);
                if (triggerBtn) {
                    triggerBtn.disabled = false;
                    triggerBtn.classList.remove('opacity-50');
                }
            });
    }

    /**
     * Synchronize a specific item card on the /cart/ page after an update.
     */
    function syncCartPageItem(key, data) {
        const itemRow = document.querySelector(`[data-cart-item-key="${CSS.escape(key)}"]`);
        if (!itemRow) return;

        const matchingItem = (data.items || []).find(it => it.key === key);
        if (!matchingItem || matchingItem.quantity <= 0) {
            // Item was removed
            itemRow.classList.add('opacity-0', 'scale-95', 'transition-all', 'duration-300');
            setTimeout(() => itemRow.remove(), 300);
        } else {
            // Update quantity display
            const qtyDisplay = itemRow.querySelector('[data-cart-qty]');
            if (qtyDisplay) qtyDisplay.textContent = matchingItem.quantity;

            // Update item total display
            const totalDisplay = itemRow.querySelector('[data-cart-item-total]');
            if (totalDisplay) totalDisplay.textContent = `৳${parseFloat(matchingItem.total).toFixed(2)}`;
        }

        // Update items count in sub-header
        const countDisplay = document.getElementById('cart-page-items-count');
        if (countDisplay) {
            countDisplay.textContent = `${data.cart_count} meal portion(s) in cart`;
        }
    }

    /**
     * Refresh drawer items from the server.
     */
    function refreshCartDrawer() {
        fetch('/api/cart/items/', {
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json'
            }
        })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    updateCartUI(data);
                    renderDrawerItems(data);
                }
            })
            .catch(err => console.error('Drawer refresh error:', err));
    }

    /**
     * Synchronize UI totals, badge, progress bar, and buttons across DOM.
     */
    function updateCartUI(data) {
        const subtotal = parseFloat(data.subtotal || 0);
        const deliveryFee = parseFloat(data.delivery_fee || 0);
        const total = parseFloat(data.total || 0);
        const cartCount = parseInt(data.cart_count || 0, 10);
        const minOrder = parseFloat(data.minimum_order_amount || 0);
        const freeDeliveryPercent = Math.min(100, Math.max(0, data.free_delivery_percent || 0));
        const freeDeliveryRemaining = parseFloat(data.free_delivery_remaining || 0);

        // 1. Navigation Badges
        const navBadges = document.querySelectorAll('.nav-cart-badge-count');
        navBadges.forEach(badge => {
            badge.textContent = cartCount;
            const container = badge.closest('.nav-cart-badge') || badge;
            if (cartCount > 0) {
                container.classList.remove('hidden');
            } else {
                container.classList.add('hidden');
            }
        });

        const headerNavBadge = document.getElementById('nav-cart-badge');
        if (headerNavBadge) {
            headerNavBadge.textContent = cartCount;
            if (cartCount > 0) {
                headerNavBadge.classList.remove('hidden');
            } else {
                headerNavBadge.classList.add('hidden');
            }
        }

        // 2. Floating Cart Elements
        const floatingBadge = document.getElementById('floating-cart-badge');
        if (floatingBadge) {
            floatingBadge.textContent = cartCount;
            if (cartCount > 0) {
                floatingBadge.classList.remove('hidden');
            } else {
                floatingBadge.classList.add('hidden');
            }
        }

        const floatingItemsText = document.getElementById('floating-cart-items-text');
        if (floatingItemsText) {
            floatingItemsText.textContent = `${cartCount} item${cartCount === 1 ? '' : 's'}`;
        }

        const floatingSubtotal = document.getElementById('floating-cart-subtotal');
        if (floatingSubtotal) {
            floatingSubtotal.textContent = subtotal.toFixed(2);
        }

        const floatingBtn = document.getElementById('floating-cart-btn');
        if (floatingBtn) {
            floatingBtn.setAttribute('aria-label', `Shopping Cart with ${cartCount} item${cartCount === 1 ? '' : 's'}, Subtotal ৳${subtotal.toFixed(2)}`);
        }

        // 2. Drawer Totals
        const drawerSubtotal = document.getElementById('drawer-subtotal');
        if (drawerSubtotal) drawerSubtotal.textContent = subtotal.toFixed(2);

        const drawerDelivery = document.getElementById('drawer-delivery');
        if (drawerDelivery) drawerDelivery.textContent = deliveryFee.toFixed(2);

        const drawerTotal = document.getElementById('drawer-total');
        if (drawerTotal) drawerTotal.textContent = total.toFixed(2);

        // Drawer Free Delivery Progress Bar
        const drawerProgressBar = document.getElementById('free-delivery-progress');
        if (drawerProgressBar) {
            drawerProgressBar.style.width = freeDeliveryPercent + '%';
            if (freeDeliveryPercent >= 100) {
                drawerProgressBar.classList.remove('bg-byte-amber');
                drawerProgressBar.classList.add('bg-emerald-500');
            } else {
                drawerProgressBar.classList.remove('bg-emerald-500');
                drawerProgressBar.classList.add('bg-byte-amber');
            }
        }

        const drawerProgressText = document.getElementById('free-delivery-text');
        if (drawerProgressText) {
            if (freeDeliveryRemaining <= 0) {
                drawerProgressText.textContent = '🎉 You qualify for FREE Delivery!';
            } else {
                drawerProgressText.textContent = `Add ৳${freeDeliveryRemaining.toFixed(0)} more for Free Delivery!`;
            }
        }

        // Drawer Checkout Button State
        const drawerCheckoutBtn = document.getElementById('drawer-checkout-btn');
        if (drawerCheckoutBtn) {
            if (cartCount === 0) {
                drawerCheckoutBtn.classList.add('opacity-50', 'pointer-events-none');
                drawerCheckoutBtn.setAttribute('title', 'Your cart is empty');
            } else if (!data.can_checkout) {
                drawerCheckoutBtn.classList.add('opacity-50', 'pointer-events-none');
                drawerCheckoutBtn.setAttribute('title', `Minimum order requirement is ৳${minOrder.toFixed(0)}`);
            } else {
                drawerCheckoutBtn.classList.remove('opacity-50', 'pointer-events-none');
                drawerCheckoutBtn.removeAttribute('title');
            }
        }

        // 3. Cart Page Sync (/cart/)
        const cartPageSubtotal = document.getElementById('cart-page-subtotal');
        if (cartPageSubtotal) cartPageSubtotal.textContent = subtotal.toFixed(2);

        const cartPageDelivery = document.getElementById('cart-page-delivery');
        if (cartPageDelivery) cartPageDelivery.textContent = deliveryFee.toFixed(2);

        const cartPageTotal = document.getElementById('cart-page-total');
        if (cartPageTotal) cartPageTotal.textContent = total.toFixed(2);

        const checkoutTotalSpan = document.getElementById('cart-page-checkout-total');
        if (checkoutTotalSpan) checkoutTotalSpan.textContent = total.toFixed(2);

        // Cart Page Free Delivery Bar
        const cpProgress = document.getElementById('cart-page-fd-progress');
        if (cpProgress) {
            cpProgress.style.width = freeDeliveryPercent + '%';
            if (freeDeliveryPercent >= 100) {
                cpProgress.classList.remove('bg-byte-amber');
                cpProgress.classList.add('bg-emerald-500');
            } else {
                cpProgress.classList.remove('bg-emerald-500');
                cpProgress.classList.add('bg-byte-amber');
            }
        }

        const cpText = document.getElementById('cart-page-fd-text');
        if (cpText) {
            if (freeDeliveryRemaining <= 0) {
                cpText.textContent = '🎉 Free Delivery Unlocked!';
            } else {
                cpText.textContent = `Add ৳${freeDeliveryRemaining.toFixed(0)} more for Free Delivery!`;
            }
        }

        // Cart Page Checkout Container
        const checkoutContainer = document.getElementById('cart-page-checkout-container');
        if (checkoutContainer) {
            checkoutContainer.innerHTML = '';
            if (cartCount === 0) {
                const emptyBtn = document.createElement('button');
                emptyBtn.disabled = true;
                emptyBtn.className = 'w-full py-3.5 rounded-2xl bg-gray-300 text-gray-500 font-bold text-sm cursor-not-allowed';
                emptyBtn.textContent = 'Your Cart is Empty';
                checkoutContainer.appendChild(emptyBtn);
            } else if (!data.can_checkout) {
                const warningDiv = document.createElement('div');
                warningDiv.className = 'p-3 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs font-semibold flex items-start gap-2 mb-3';
                const warnIcon = document.createElement('i');
                warnIcon.className = 'fa-solid fa-triangle-exclamation text-base mt-0.5 shrink-0';
                const warnText = document.createElement('span');
                warnText.className = 'break-words whitespace-normal leading-snug';
                warnText.textContent = `Minimum order requirement is ৳${minOrder.toFixed(0)}. Please add more items.`;
                warningDiv.appendChild(warnIcon);
                warningDiv.appendChild(warnText);

                const disabledBtn = document.createElement('button');
                disabledBtn.disabled = true;
                disabledBtn.className = 'w-full py-3.5 px-4 rounded-2xl bg-gray-300 text-gray-500 font-bold text-sm cursor-not-allowed whitespace-normal';
                disabledBtn.textContent = 'Proceed to Checkout';

                checkoutContainer.appendChild(warningDiv);
                checkoutContainer.appendChild(disabledBtn);
            } else {
                const checkoutLink = document.createElement('a');
                checkoutLink.href = '/checkout/';
                checkoutLink.className = 'block w-full py-3.5 sm:py-4 px-4 rounded-2xl bg-byte-amber hover:bg-byte-amberDark text-white font-extrabold text-sm text-center shadow-lg hover:shadow-xl transition transform hover:-translate-y-0.5 whitespace-normal break-words leading-snug';
                checkoutLink.textContent = `Proceed to Checkout (৳${total.toFixed(2)})`;
                checkoutContainer.appendChild(checkoutLink);
            }
        }

        // Render Cart Page Empty State if cart emptied
        if (cartCount === 0) {
            const mainContainer = document.getElementById('cart-items-container');
            if (mainContainer && !mainContainer.querySelector('.empty-cart-state')) {
                mainContainer.innerHTML = `
                    <div class="empty-cart-state bg-white rounded-2xl sm:rounded-3xl p-6 sm:p-12 text-center border border-gray-200 max-w-xl mx-auto shadow-sm">
                        <div class="w-16 h-16 sm:w-20 sm:h-20 rounded-full bg-byte-cream text-byte-maroon mx-auto flex items-center justify-center text-2xl sm:text-3xl mb-4">
                            <i class="fa-solid fa-utensils"></i>
                        </div>
                        <h3 class="font-display text-xl sm:text-2xl font-bold text-byte-maroon mb-2 break-words">Your Cart is Empty</h3>
                        <p class="text-xs sm:text-sm text-gray-500 mb-6 break-words">Looks like you haven't added any homestyle delicious food yet.</p>
                        <a href="/menu/" class="inline-flex items-center justify-center gap-2 px-6 sm:px-8 py-3.5 rounded-full bg-byte-amber hover:bg-byte-amberDark text-white font-extrabold text-xs sm:text-sm tracking-wide shadow-lg transition whitespace-normal text-center">
                            <span>Browse Today's Menu</span>
                            <i class="fa-solid fa-arrow-right text-xs"></i>
                        </a>
                    </div>
                `;
            }
        }
    }

    /**
     * Render items inside the slide-out Cart Drawer.
     */
    function renderDrawerItems(data) {
        const drawerContainer = document.getElementById('cart-drawer-items');
        if (!drawerContainer) return;

        drawerContainer.innerHTML = '';

        if (!data.items || data.items.length === 0) {
            const emptyWrap = document.createElement('div');
            emptyWrap.className = 'text-center py-12 text-gray-400';

            const icon = document.createElement('i');
            icon.className = 'fa-solid fa-utensils text-4xl mb-3 text-byte-maroon/20';

            const p = document.createElement('p');
            p.className = 'font-medium text-sm';
            p.textContent = 'Your cart is currently empty.';

            const a = document.createElement('a');
            a.href = '/menu/';
            a.className = 'inline-block mt-3 px-5 py-2.5 rounded-full bg-byte-maroon text-white text-xs font-bold hover:bg-byte-maroonDark transition';
            a.textContent = 'Browse Daily Menu';
            a.addEventListener('click', closeCartDrawer);

            emptyWrap.appendChild(icon);
            emptyWrap.appendChild(p);
            emptyWrap.appendChild(a);
            drawerContainer.appendChild(emptyWrap);
            return;
        }

        data.items.forEach(item => {
            const card = document.createElement('div');
            card.className = 'flex flex-wrap xs:flex-nowrap items-start justify-between p-3 rounded-2xl bg-gray-50 border border-gray-100 gap-2.5 sm:gap-3';
            card.dataset.cartKey = item.key;

            // Thumbnail
            const imgWrap = document.createElement('div');
            imgWrap.className = 'w-14 h-14 rounded-xl bg-gray-200 overflow-hidden flex-shrink-0';
            const img = document.createElement('img');
            img.src = item.image || '/static/images/hero_banner.png';
            img.alt = item.name;
            img.className = 'w-full h-full object-cover';
            imgWrap.appendChild(img);

            // Details
            const details = document.createElement('div');
            details.className = 'flex-1 min-w-0';

            const nameH4 = document.createElement('h4');
            nameH4.className = 'font-display font-bold text-sm text-byte-maroon break-words whitespace-normal leading-snug';
            nameH4.textContent = item.name;

            const portionSpan = document.createElement('span');
            portionSpan.className = 'text-[11px] text-gray-500 block break-words whitespace-normal';
            portionSpan.textContent = item.portion_size || '';

            details.appendChild(nameH4);
            details.appendChild(portionSpan);

            if (item.addons && item.addons.length > 0) {
                const addonsSpan = document.createElement('span');
                addonsSpan.className = 'text-[10px] text-byte-amber font-semibold block break-words whitespace-normal leading-snug mt-0.5';
                addonsSpan.textContent = '+ ' + item.addons.join(', ');
                details.appendChild(addonsSpan);
            }

            if (item.special_instructions) {
                const notesSpan = document.createElement('span');
                notesSpan.className = 'text-[10px] text-gray-500 italic block break-words whitespace-normal leading-snug mt-0.5';
                notesSpan.textContent = `"${item.special_instructions}"`;
                details.appendChild(notesSpan);
            }

            const priceSpan = document.createElement('span');
            priceSpan.className = 'text-xs font-black text-gray-900 block mt-1';
            priceSpan.textContent = `৳${parseFloat(item.price).toFixed(2)}`;
            details.appendChild(priceSpan);

            // Controls
            const controls = document.createElement('div');
            controls.className = 'flex xs:flex-col items-center xs:items-end justify-between w-full xs:w-auto gap-2 xs:gap-1.5 pt-2 xs:pt-0 border-t xs:border-t-0 border-gray-200/60 flex-shrink-0';

            const qtyGroup = document.createElement('div');
            qtyGroup.className = 'flex items-center border border-gray-300 rounded-lg overflow-hidden bg-white';

            const minusBtn = document.createElement('button');
            minusBtn.type = 'button';
            minusBtn.className = 'w-7 h-7 hover:bg-gray-100 text-gray-700 font-bold transition flex items-center justify-center text-xs';
            minusBtn.textContent = '-';
            minusBtn.setAttribute('aria-label', `Decrease quantity of ${item.name}`);
            minusBtn.addEventListener('click', () => changeCartQty(item.key, -1, minusBtn));

            const qtySpan = document.createElement('span');
            qtySpan.className = 'w-7 text-center text-xs font-bold text-gray-900';
            qtySpan.textContent = item.quantity;

            const plusBtn = document.createElement('button');
            plusBtn.type = 'button';
            plusBtn.className = 'w-7 h-7 hover:bg-gray-100 text-gray-700 font-bold transition flex items-center justify-center text-xs';
            plusBtn.textContent = '+';
            plusBtn.setAttribute('aria-label', `Increase quantity of ${item.name}`);
            plusBtn.addEventListener('click', () => changeCartQty(item.key, 1, plusBtn));

            qtyGroup.appendChild(minusBtn);
            qtyGroup.appendChild(qtySpan);
            qtyGroup.appendChild(plusBtn);

            const bottomRow = document.createElement('div');
            bottomRow.className = 'flex items-center gap-2';

            const itemTotalSpan = document.createElement('span');
            itemTotalSpan.className = 'text-xs font-black text-byte-maroon';
            itemTotalSpan.textContent = `৳${parseFloat(item.total).toFixed(2)}`;

            const trashBtn = document.createElement('button');
            trashBtn.type = 'button';
            trashBtn.className = 'text-gray-400 hover:text-rose-600 transition';
            trashBtn.setAttribute('title', 'Remove item');
            trashBtn.setAttribute('aria-label', `Remove ${item.name} from cart`);
            trashBtn.innerHTML = '<i class="fa-solid fa-trash-can text-xs"></i>';
            trashBtn.addEventListener('click', () => removeCartItem(item.key, trashBtn));

            bottomRow.appendChild(itemTotalSpan);
            bottomRow.appendChild(trashBtn);

            controls.appendChild(qtyGroup);
            controls.appendChild(bottomRow);

            card.appendChild(imgWrap);
            card.appendChild(details);
            card.appendChild(controls);

            drawerContainer.appendChild(card);
        });
    }

    /**
     * Intercept and enhance standard HTML fallback forms for progressive enhancement.
     */
    function attachFormProgressiveEnhancement() {
        // Intercept cart add forms (if any)
        document.addEventListener('submit', function (e) {
            const form = e.target;
            if (form.matches('.ajax-cart-add-form')) {
                e.preventDefault();
                const itemId = form.querySelector('[name=item_id]')?.value;
                const qty = form.querySelector('[name=quantity]')?.value || 1;
                const instructions = form.querySelector('[name=special_instructions]')?.value || '';
                const submitBtn = form.querySelector('button[type=submit]');
                if (itemId) {
                    addToCart(itemId, qty, instructions, [], submitBtn);
                }
            } else if (form.matches('.ajax-cart-update-form')) {
                e.preventDefault();
                const key = form.querySelector('[name=key]')?.value;
                const delta = form.querySelector('[name=delta]')?.value;
                const submitBtn = form.querySelector('button[type=submit]');
                if (key && delta !== undefined) {
                    changeCartQty(key, parseInt(delta, 10), submitBtn);
                }
            } else if (form.matches('.ajax-cart-remove-form')) {
                e.preventDefault();
                const key = form.querySelector('[name=key]')?.value;
                const submitBtn = form.querySelector('button[type=submit]');
                if (key) {
                    removeCartItem(key, submitBtn);
                }
            }
        });
    }

    /**
     * Mobile Menu initialization.
     */
    function initMobileMenu() {
        const mobileBtn = document.getElementById('mobile-menu-btn');
        const mobileMenu = document.getElementById('mobile-menu');
        if (!mobileBtn || !mobileMenu) return;

        function setMobileMenuOpen(isOpen) {
            mobileMenu.classList.toggle('hidden', !isOpen);
            mobileBtn.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            const icon = mobileBtn.querySelector('i');
            if (icon) {
                icon.className = isOpen ? 'fa-solid fa-xmark text-lg' : 'fa-solid fa-bars text-lg';
            }
        }

        mobileBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const willOpen = mobileMenu.classList.contains('hidden');
            setMobileMenuOpen(willOpen);
        });

        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', () => {
                setMobileMenuOpen(false);
            });
        });

        document.addEventListener('click', function (e) {
            if (!mobileMenu.contains(e.target) && !mobileBtn.contains(e.target)) {
                setMobileMenuOpen(false);
            }
        });
    }

    /**
     * Global keyboard shortcuts (Escape closes modals & drawer).
     */
    function initKeyboardListeners() {
        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape') {
                closeItemModal();
                closeCartDrawer();
                const reviewModal = document.getElementById('review-modal');
                if (reviewModal) reviewModal.classList.add('hidden');
            }
        });
    }

    // Expose functions globally for backward-compatibility with template onclick attributes
    window.ByteCart = {
        getCsrfToken,
        showToast,
        openItemModal,
        closeItemModal,
        adjustModalQty,
        recalcModalTotal,
        submitModalAddToCart,
        openCartDrawer,
        closeCartDrawer,
        toggleCartDrawer,
        addToCart,
        changeCartQty,
        updateCartQty,
        removeCartItem,
        refreshCartDrawer,
        updateCartUI
    };

    // Alias window helpers for seamless compatibility
    window.openItemModal = openItemModal;
    window.closeItemModal = closeItemModal;
    window.adjustModalQty = adjustModalQty;
    window.recalcModalTotal = recalcModalTotal;
    window.submitModalAddToCart = submitModalAddToCart;
    window.openCartDrawer = openCartDrawer;
    window.closeCartDrawer = closeCartDrawer;
    window.toggleCartDrawer = toggleCartDrawer;
    window.addToCart = addToCart;
    window.changeCartQty = changeCartQty;
    window.updateCartQty = updateCartQty;
    window.removeCartItem = removeCartItem;
    window.refreshCartDrawer = refreshCartDrawer;
    window.showToast = showToast;
    window.getCsrfToken = getCsrfToken;

    // Initialize upon DOM readiness
    document.addEventListener('DOMContentLoaded', function () {
        initMobileMenu();
        initKeyboardListeners();
        attachFormProgressiveEnhancement();
        refreshCartDrawer();
    });

})();

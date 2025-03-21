// Toast Notification System
function showToast(message, type = 'success') {
    const toast = document.createElement('div');
    toast.className = `toast align-items-center text-white bg-${type} border-0 position-fixed bottom-0 end-0 m-3`;
    toast.setAttribute('role', 'alert');
    toast.setAttribute('aria-live', 'assertive');
    toast.setAttribute('aria-atomic', 'true');
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    document.body.appendChild(toast);
    const bsToast = new bootstrap.Toast(toast);
    bsToast.show();
    
    toast.addEventListener('hidden.bs.toast', () => {
        toast.remove();
    });
}

// Cart Functionality
class Cart {
    constructor() {
        this.items = JSON.parse(localStorage.getItem('cart')) || [];
        this.updateCartBadge();
    }
    
    addItem(product) {
        const existingItem = this.items.find(item => item.id === product.id);
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.items.push({ ...product, quantity: 1 });
        }
        this.saveCart();
        this.updateCartBadge();
        showToast('Product added to cart');
    }
    
    removeItem(productId) {
        this.items = this.items.filter(item => item.id !== productId);
        this.saveCart();
        this.updateCartBadge();
        showToast('Product removed from cart');
    }
    
    updateQuantity(productId, quantity) {
        const item = this.items.find(item => item.id === productId);
        if (item) {
            item.quantity = Math.max(1, quantity);
            this.saveCart();
            this.updateCartBadge();
        }
    }
    
    getTotal() {
        return this.items.reduce((total, item) => total + (item.price * item.quantity), 0);
    }
    
    saveCart() {
        localStorage.setItem('cart', JSON.stringify(this.items));
    }
    
    updateCartBadge() {
        const badge = document.querySelector('.cart-badge');
        if (badge) {
            const totalItems = this.items.reduce((total, item) => total + item.quantity, 0);
            badge.textContent = totalItems;
            badge.style.display = totalItems > 0 ? 'block' : 'none';
        }
    }
}

// Initialize Cart
const cart = new Cart();

// Product Image Gallery
function initProductGallery() {
    const gallery = document.querySelector('.product-gallery');
    if (gallery) {
        const mainImage = gallery.querySelector('.main-image');
        const thumbnails = gallery.querySelectorAll('.thumbnail');
        
        thumbnails.forEach(thumb => {
            thumb.addEventListener('click', () => {
                mainImage.src = thumb.src;
                thumbnails.forEach(t => t.classList.remove('active'));
                thumb.classList.add('active');
            });
        });
    }
}

// Quantity Input
function initQuantityInput() {
    const quantityInputs = document.querySelectorAll('.quantity-input');
    quantityInputs.forEach(input => {
        const minusBtn = input.querySelector('.minus');
        const plusBtn = input.querySelector('.plus');
        const numberInput = input.querySelector('input');
        
        minusBtn.addEventListener('click', () => {
            const currentValue = parseInt(numberInput.value);
            if (currentValue > 1) {
                numberInput.value = currentValue - 1;
                numberInput.dispatchEvent(new Event('change'));
            }
        });
        
        plusBtn.addEventListener('click', () => {
            const currentValue = parseInt(numberInput.value);
            numberInput.value = currentValue + 1;
            numberInput.dispatchEvent(new Event('change'));
        });
    });
}

// Review Form
function initReviewForm() {
    const form = document.querySelector('.review-form');
    if (form) {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const formData = new FormData(form);
            
            try {
                const response = await fetch('/api/reviews/', {
                    method: 'POST',
                    body: formData,
                    headers: {
                        'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                    }
                });
                
                if (response.ok) {
                    showToast('Review submitted successfully');
                    form.reset();
                } else {
                    showToast('Error submitting review', 'danger');
                }
            } catch (error) {
                showToast('Error submitting review', 'danger');
            }
        });
    }
}

// Star Rating
function initStarRating() {
    const ratingContainers = document.querySelectorAll('.star-rating');
    ratingContainers.forEach(container => {
        const stars = container.querySelectorAll('.star');
        const input = container.querySelector('input');
        
        stars.forEach(star => {
            star.addEventListener('click', () => {
                const rating = star.dataset.rating;
                input.value = rating;
                stars.forEach(s => {
                    s.classList.toggle('active', s.dataset.rating <= rating);
                });
            });
            
            star.addEventListener('mouseover', () => {
                const rating = star.dataset.rating;
                stars.forEach(s => {
                    s.classList.toggle('active', s.dataset.rating <= rating);
                });
            });
        });
        
        container.addEventListener('mouseout', () => {
            const rating = input.value;
            stars.forEach(s => {
                s.classList.toggle('active', s.dataset.rating <= rating);
            });
        });
    });
}

// Search Autocomplete
function initSearchAutocomplete() {
    const searchInput = document.querySelector('.search-input');
    if (searchInput) {
        let timeout;
        searchInput.addEventListener('input', () => {
            clearTimeout(timeout);
            timeout = setTimeout(async () => {
                const query = searchInput.value.trim();
                if (query.length >= 2) {
                    try {
                        const response = await fetch(`/api/search/?q=${encodeURIComponent(query)}`);
                        const data = await response.json();
                        updateSearchResults(data);
                    } catch (error) {
                        console.error('Search error:', error);
                    }
                } else {
                    clearSearchResults();
                }
            }, 300);
        });
    }
}

function updateSearchResults(results) {
    const container = document.querySelector('.search-results');
    if (container) {
        container.innerHTML = results.map(product => `
            <a href="/products/${product.id}/" class="search-result-item">
                <img src="${product.image}" alt="${product.name}">
                <div>
                    <h6>${product.name}</h6>
                    <p class="text-muted">$${product.price}</p>
                </div>
            </a>
        `).join('');
        container.style.display = 'block';
    }
}

function clearSearchResults() {
    const container = document.querySelector('.search-results');
    if (container) {
        container.innerHTML = '';
        container.style.display = 'none';
    }
}

// Initialize all components when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    initProductGallery();
    initQuantityInput();
    initReviewForm();
    initStarRating();
    initSearchAutocomplete();
}); 